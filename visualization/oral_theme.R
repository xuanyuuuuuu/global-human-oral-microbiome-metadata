suppressPackageStartupMessages({
  library(ggplot2)
  library(scales)
})

theme_oral <- function(base_size = 12, base_family = "sans") {
  theme_bw(base_size = base_size, base_family = base_family) +
    theme(
      axis.title = element_text(size = base_size + 4),
      axis.text  = element_text(size = base_size),
      panel.grid.major   = element_line(colour = "grey85", linewidth = 0.4),
      panel.grid.minor.x = element_line(colour = "grey93", linewidth = 0.3),
      panel.grid.minor.y = element_blank(),
      legend.title = element_text(size = base_size + 2),
      legend.text  = element_text(size = base_size),
      legend.position = "right"
    )
}

scale_x_oral_years <- function(year_min = 2011, year_max = 2025) {
  scale_x_continuous(
    breaks = c(2011, 2015, 2020, 2025),
    minor_breaks = year_min:year_max,
    limits = c(year_min - 0.5, year_max + 0.5),
    expand = expansion(mult = c(0, 0.01))
  )
}

scale_y_oral_prop <- function() {
  scale_y_continuous(
    limits = c(0, 1),
    breaks = seq(0, 1, 0.25),
    labels = percent_format(accuracy = 1),
    expand = expansion(mult = c(0.05, 0))
  )
}

scale_y_oral_count <- function() {
  scale_y_continuous(
    labels = comma_format(accuracy = 1),
    expand = expansion(mult = c(0.05, 0))
  )
}

save_oral_fig <- function(p, filename, width = 10, height = 5) {
  dir.create(dirname(filename), showWarnings = FALSE, recursive = TRUE)
  if (grepl("\\.svg$", filename, ignore.case = TRUE) && requireNamespace("svglite", quietly = TRUE)) {
    ggsave(filename, plot = p, width = width, height = height, dpi = 300, device = svglite::svglite, bg = "white")
  } else {
    ggsave(filename, plot = p, width = width, height = height, dpi = 300, bg = "white")
  }
}