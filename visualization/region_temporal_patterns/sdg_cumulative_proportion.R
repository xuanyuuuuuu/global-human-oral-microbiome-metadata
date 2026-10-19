# ============================================
# Figure: Cumulative proportion by SDG region
# ============================================

if (!exists("args", inherits = FALSE)) {
  args <- commandArgs(trailingOnly = TRUE)
}

get_arg <- function(k, default = NULL) {
  i <- which(args == k)
  if (length(i) == 0) return(default)
  if (i == length(args)) return(default)
  args[i + 1]
}

biosample_path <- get_arg("--biosample")
country_path   <- get_arg("--country")
theme_path     <- get_arg("--theme")
outfile        <- get_arg("--out")

if (is.null(biosample_path) || is.null(country_path) || is.null(theme_path) || is.null(outfile)) {
  stop(
    paste(
      "Usage:",
      "Rscript figure1D_sdg_cumulative_proportion.R",
      "--biosample final_biosample.csv",
      "--country country_population_group.csv",
      "--theme oral_theme.R",
      "--out figure1D_sdg_cumulative_proportion.svg"
    )
  )
}

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(lubridate)
  library(scales)
})

source(theme_path)

bios <- read_csv(biosample_path, show_col_types = FALSE)
country_info <- read_csv(country_path, show_col_types = FALSE)

required_bios_cols <- c("country_clean", "release_date")
required_country_cols <- c("country_clean", "SDG_Region")

missing_bios <- setdiff(required_bios_cols, names(bios))
missing_country <- setdiff(required_country_cols, names(country_info))

if (length(missing_bios) > 0) {
  stop(paste("Missing columns in biosample file:", paste(missing_bios, collapse = ", ")))
}
if (length(missing_country) > 0) {
  stop(paste("Missing columns in country file:", paste(missing_country, collapse = ", ")))
}

bios_year <- bios |>
  mutate(
    country_clean = trimws(as.character(country_clean)),
    date_clean = as.Date(substr(as.character(release_date), 1, 10)),
    year = year(date_clean)
  ) |>
  select(country_clean, year)

country_sdg <- country_info |>
  mutate(
    country_clean = trimws(as.character(country_clean)),
    SDG_Region = trimws(as.character(SDG_Region))
  ) |>
  select(country_clean, SDG_Region)

bios_sdg <- bios_year |>
  left_join(country_sdg, by = "country_clean") |>
  filter(
    !is.na(year),
    !is.na(SDG_Region),
    !SDG_Region %in% c("Unreported", "(Unreported)")
  )

year_min <- 2011
year_max <- 2025

sdg_year <- bios_sdg |>
  filter(year >= year_min, year <= year_max) |>
  count(SDG_Region, year, name = "n_year") |>
  complete(
    SDG_Region,
    year = year_min:year_max,
    fill = list(n_year = 0)
  ) |>
  group_by(SDG_Region) |>
  arrange(year, .by_group = TRUE) |>
  mutate(cum_samples = cumsum(n_year)) |>
  ungroup()

sdg_order <- sdg_year |>
  filter(year == year_max) |>
  arrange(desc(cum_samples)) |>
  pull(SDG_Region)

sdg_year <- sdg_year |>
  mutate(SDG_Region = factor(SDG_Region, levels = sdg_order))

sdg_prop_cum <- sdg_year |>
  group_by(year) |>
  mutate(
    total_cum = sum(cum_samples),
    prop_cum = ifelse(total_cum > 0, cum_samples / total_cum, NA_real_)
  ) |>
  ungroup()

sdg_colors <- c(
  "#4C72B0",
  "#F4A7A0",
  "#F2D58A",
  "#9FC9A3",
  "#A5BDE0",
  "#B3A3C9",
  "#B78B72",
  "#E9A36B"
)
names(sdg_colors) <- sdg_order

p <- ggplot(
  sdg_prop_cum,
  aes(x = year, y = prop_cum, fill = SDG_Region)
) +
  geom_col(width = 0.8, colour = NA) +
  scale_x_oral_years(year_min = year_min, year_max = year_max) +
  scale_y_oral_prop() +
  scale_fill_manual(values = sdg_colors) +
  labs(
    x = "Year",
    y = "Proportion of total samples",
    fill = "SDG region"
  ) +
  theme_oral()

save_oral_fig(p, outfile, width = 10, height = 5)

print(p)