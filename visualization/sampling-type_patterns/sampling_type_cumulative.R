# ============================================
# Figure 1F: Cumulative samples by sampling type
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
theme_path     <- get_arg("--theme")
outfile        <- get_arg("--out")

if (is.null(biosample_path) || is.null(theme_path) || is.null(outfile)) {
  stop(
    paste(
      "Usage:",
      "Rscript figure1F_sampling_type_cumulative.R",
      "--biosample final_biosample.csv",
      "--theme oral_theme.R",
      "--out figure1F_sampling_type_cumulative.svg"
    )
  )
}

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(lubridate)
})

source(theme_path)

bios <- read_csv(biosample_path, show_col_types = FALSE)

required_bios_cols <- c("sampling_type_main_category", "release_date")
missing_bios <- setdiff(required_bios_cols, names(bios))

if (length(missing_bios) > 0) {
  stop(paste("Missing columns in biosample file:", paste(missing_bios, collapse = ", ")))
}

df <- bios |>
  mutate(
    sampling_type_main_category = trimws(as.character(sampling_type_main_category)),
    date_clean = as.Date(substr(as.character(release_date), 1, 10)),
    year = year(date_clean)
  ) |>
  filter(
    !is.na(year),
    !is.na(sampling_type_main_category),
    !sampling_type_main_category %in% c("Unspecified", "Unknown")
  )

year_min <- 2011
year_max <- 2025

type_cols <- c(
  "Oral Fluids" = "#F4A7A0",
  "Dental Plaque and Calculus" = "#4C72B0",
  "Oral Mucosa and Surfaces" = "#A5BDE0",
  "Special/Lesion Sites" = "#B3A3C9"
)

type_year <- df |>
  filter(year >= year_min, year <= year_max) |>
  count(sampling_type_main_category, year, name = "n_year")

type_cum <- type_year |>
  complete(
    sampling_type_main_category,
    year = year_min:year_max,
    fill = list(n_year = 0)
  ) |>
  group_by(sampling_type_main_category) |>
  arrange(year, .by_group = TRUE) |>
  mutate(cum_samples = cumsum(n_year)) |>
  ungroup()

type_order <- type_cum |>
  filter(year == year_max) |>
  arrange(desc(cum_samples)) |>
  pull(sampling_type_main_category)

type_cum <- type_cum |>
  mutate(
    sampling_type_main_category = factor(
      sampling_type_main_category,
      levels = type_order
    )
  )

p <- ggplot(
  type_cum,
  aes(x = year, y = cum_samples, colour = sampling_type_main_category)
) +
  geom_line(linewidth = 1) +
  scale_x_oral_years(year_min = year_min, year_max = year_max) +
  scale_y_oral_count() +
  scale_colour_manual(values = type_cols) +
  labs(
    x = "Year",
    y = "Cumulative samples",
    colour = "Sampling-type main category"
  ) +
  theme_oral()

save_oral_fig(p, outfile, width = 10, height = 5)

print(p)