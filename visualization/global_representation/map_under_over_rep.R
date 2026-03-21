args <- commandArgs(trailingOnly = TRUE)

get_arg <- function(k) {
  i <- which(args == k)
  if (length(i) == 0 || i == length(args)) stop("missing arg")
  args[i + 1]
}

infile <- get_arg("--input")
outfile <- get_arg("--out")

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

raw <- read_csv(infile, show_col_types = FALSE)

if ("sample_countl" %in% names(raw)) raw <- raw |> rename(Samples = sample_countl)
if ("sample_count" %in% names(raw)) raw <- raw |> rename(Samples = sample_count)
if (!("Samples" %in% names(raw))) stop("Samples missing")

if (!("log10_representation_proportion" %in% names(raw))) stop("log10_representation_proportion missing")

if (!("ISO3" %in% names(raw))) {
  if ("iso3" %in% names(raw)) raw <- raw |> rename(ISO3 = iso3)
  else stop("ISO3 missing")
}

if (!("Country" %in% names(raw))) {
  if ("country_clean" %in% names(raw)) raw <- raw |> rename(Country = country_clean)
  else if ("country" %in% names(raw)) raw <- raw |> rename(Country = country)
}

raw <- raw |> filter(is.na(Samples) | Samples > 50)

df <- raw |> mutate(Index_log = as.numeric(log10_representation_proportion))

pos_max <- suppressWarnings(max(df$Index_log[df$Index_log > 0], na.rm = TRUE))
neg_max <- suppressWarnings(max(abs(df$Index_log[df$Index_log < 0]), na.rm = TRUE))
if (!is.finite(pos_max) || pos_max <= 0) pos_max <- 1
if (!is.finite(neg_max) || neg_max <= 0) neg_max <- 1

df <- df |> mutate(
  Representation_index_scaled = case_when(
    Index_log > 0 ~ (Index_log / pos_max) * 100,
    Index_log < 0 ~ -(abs(Index_log) / neg_max) * 100,
    TRUE ~ 0
  )
)

world <- rnaturalearth::ne_countries(
  scale = "medium", type = "map_units", returnclass = "sf"
) |>
  st_make_valid() |>
  st_transform("+proj=eqearth") |>
  filter(!name_long %in% c(
    "Antarctica"
  ))

grats <- st_graticule(
  lon = seq(-180, 180, 20),
  lat = seq(-80, 80, 20)
) |> st_transform("+proj=eqearth")

world_rep <- world |>
  left_join(
    df |> select(ISO3, Country, Samples, Representation_index_scaled),
    by = c("iso_a3" = "ISO3")
  )

neg_cols <- colorRampPalette(c("#542788", "#E9E1FB"))(256)
pos_cols <- colorRampPalette(c("#F9DCD4", "#B2182B"))(256)
cols <- c(neg_cols, pos_cols)

vals_raw <- c(
  seq(-100, -1e-9, length.out = 256),
  seq(1e-9, 100, length.out = 256)
)
vals <- rescale(vals_raw, to = c(0, 1), from = c(-100, 100))

na_   <- world_rep |> filter(is.na(Representation_index_scaled))
zero  <- world_rep |> filter(!is.na(Representation_index_scaled) & Representation_index_scaled == 0)
withv <- world_rep |> filter(!is.na(Representation_index_scaled) & Representation_index_scaled != 0)

p <- ggplot() +
  geom_sf(data = grats, color = "grey85", linewidth = 0.2) +
  geom_sf(data = na_,   fill = "#2E2C8A", color = "white", linewidth = 0.25) +
  geom_sf(data = zero,  fill = "#F2F2F2", color = "white", linewidth = 0.25) +
  geom_sf(data = withv, aes(fill = Representation_index_scaled), color = "white", linewidth = 0.25) +
  scale_fill_gradientn(
    colours = cols,
    values  = vals,
    limits  = c(-100, 100),
    oob     = scales::squish,
    breaks  = c(100, -100),
    labels  = c("Overrepresented", "Underrepresented"),
    name    = "Representation",
    guide   = guide_colorbar(
      title.position = "top",
      label.position = "right",
      ticks = FALSE,
      barheight = unit(28, "mm"),
      barwidth  = unit(6,  "mm"),
      raster = TRUE
    )
  ) +
  theme_void(base_family = "sans") +
  theme(
    legend.position = c(0.10, 0.22),
    legend.justification = c(0, 0),
    legend.title = element_text(size = 10),
    legend.text  = element_text(size = 9),
    plot.margin  = margin(6, 6, 6, 6)
  )

dir.create(dirname(outfile), showWarnings = FALSE, recursive = TRUE)

if (grepl("\\.svg$", outfile, ignore.case = TRUE) && requireNamespace("svglite", quietly = TRUE)) {
  ggsave(outfile, p, width = 180, height = 120, units = "mm", device = svglite::svglite, bg = "white")
} else {
  ggsave(outfile, p, width = 180, height = 120, units = "mm", bg = "white")
}

print(p)
