args <- commandArgs(trailingOnly = TRUE)

get_arg <- function(k) {
  i <- which(args == k)
  if (length(i) == 0 || i == length(args)) stop("missing arg")
  args[i + 1]
}

biosample_path <- get_arg("--biosample")
country_path   <- get_arg("--country")
theme_path     <- get_arg("--theme")
outfile         <- get_arg("--out")

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

bios_year <- bios |>
  mutate(
    date_clean = as.Date(substr(release_date, 1, 10)),
    year = year(date_clean)
  ) |>
  select(country_clean, year)

country_sdg <- country_info |>
  select(country_clean, SDG_Region) |>
  mutate(
    country_clean = trimws(country_clean),
    SDG_Region = trimws(SDG_Region)
  )

bios_sdg <- bios_year |>
  mutate(country_clean = trimws(country_clean)) |>
  left_join(country_sdg, by = "country_clean") |>
  filter(
    !is.na(SDG_Region),
    !SDG_Region %in% c("Unreported", "(Unreported)")
  )

year_min <- 2011
year_max <- 2025

sdg_year <- bios_sdg |>
  filter(year >= year_min, year <= year_max) |>
  count(SDG_Region, year, name = "n_year")

sdg_cum <- sdg_year |>
  complete(
    SDG_Region,
    year = year_min:year_max,
    fill = list(n_year = 0)
  ) |>
  group_by(SDG_Region) |>
  arrange(year, .by_group = TRUE) |>
  mutate(cum_samples = cumsum(n_year)) |>
  ungroup()

sdg_order <- sdg_cum |>
  filter(year == year_max) |>
  arrange(desc(cum_samples)) |>
  pull(SDG_Region)

sdg_cum <- sdg_cum |>
  mutate(SDG_Region = factor(SDG_Region, levels = sdg_order))

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
  sdg_cum,
  aes(x = year, y = cum_samples, colour = SDG_Region)
) +
  geom_line(linewidth = 1) +
  scale_x_oral_years(year_min = year_min, year_max = year_max) +
  scale_y_c
