args <- commandArgs(trailingOnly = TRUE)

get_arg <- function(key, default = NULL) {
  i <- which(args == key)
  if (length(i) == 0) return(default)
  if (i == length(args)) return(default)
  args[i + 1]
}

infile <- get_arg("--input")
outfile <- get_arg("--out")

if (is.null(infile) || is.null(outfile)) {
  stop("Usage: Rscript map_country_samples.R --input country_info_all.csv --out map1.svg")
}

suppressPackageStartupMessages({
  library(ggplot2)
  library(sf)
  library(rnaturalearth)
  library(readr)
  library(dplyr)
  library(scales)
  library(units)
})

sf::sf_use_s2(FALSE)

world <- rnaturalearth::ne_countries(scale = "medium", returnclass = "sf") |>
  st_make_valid() |>
  st_transform("+proj=eqearth")

grats <- st_graticule(
  lon = seq(-180, 180, by = 20),
  lat = seq(-80, 80, by = 20)
) |>
  st_transform("+proj=eqearth")

samples <- read_csv(infile, show_col_types = FALSE) |>
  transmute(
    iso3,
    Samples = as.numeric(sample_count)
  )

world_merged <- left_join(world, samples, by = c("iso_a3" = "iso3")) |>
  mutate(Samples_plot = ifelse(!is.na(Samples) & Samples > 0, Samples, NA_real_))

p <- ggplot() +
  geom_sf(data = grats, color = "grey85", linewidth = 0.2) +
  geom_sf(data = world_merged, aes(fill = Samples_plot), color = "white", linewidth = 0.2) +
  scale_fill_gradient(
    trans = "log10",
    low = "#e6f2ff",
    high = "#084594",
    breaks = c(1, 10, 100, 1000, 10000),
    labels = label_number(accuracy = 1, big.mark = ","),
    na.value = "#f0f0f0",
    name = "Samples"
  ) +
  theme_void(base_family = "sans") +
  guides(fill = guide_colorbar(
    title = "Samples",
    barheight = unit(22, "mm"),
    barwidth = unit(4, "mm"),
    ticks.colour = "grey50"
  )) +
  theme(
    legend.position = c(0.10, 0.18),
    legend.justification = c(0, 0),
    legend.background = element_rect(fill = "transparent", color = NA),
    legend.title = element_text(size = 9),
    legend.text = element_text(size = 8),
    plot.margin = margin(5, 5, 5, 5)
  )

dir.create(dirname(outfile), showWarnings = FALSE, recursive = TRUE)

if (grepl("\\.svg$", outfile, ignore.case = TRUE) && requireNamespace("svglite", quietly = TRUE)) {
  ggsave(filename = outfile, plot = p, width = 180, height = 120, units = "mm", device = svglite::svglite, bg = "white")
} else {
  ggsave(filename = outfile, plot = p, width = 180, height = 120, units = "mm", bg = "white")
}

print(p)
