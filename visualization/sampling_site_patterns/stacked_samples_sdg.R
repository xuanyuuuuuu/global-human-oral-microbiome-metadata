args <- commandArgs(trailingOnly = TRUE)

get_arg <- function(k) {
  i <- which(args == k)
  if (length(i) == 0 || i == length(args)) stop("missing arg")
  args[i + 1]
}

infile <- get_arg("--input")
outfile <- get_arg("--out")

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
})

bios <- read_csv(infile, show_col_types = FALSE)

if (!"sampling_site_main_category" %in% names(bios)) stop("sampling_site_main_category missing")

df <- bios |>
  mutate(sampling_site_main_category = trimws(as.character(sampling_site_main_category))) |>
  filter(
    !is.na(sampling_site_main_category),
    !sampling_site_main_category %in% c("Unspecified", "Unknown")
  )

site_cols <- c(
  "Oral Fluids" = "#F4A7A0",
  "Dental Plaque and Calculus" = "#4C72B0",
  "Oral Mucosa and Surfaces" = "#A5BDE0",
  "Special/Lesion Sites" = "#B3A3C9"
)

site_summary <- df |>
  count(sampling_site_main_category, name = "n") |>
  mutate(
    sampling_site_main_category = factor(sampling_site_main_category, levels = names(site_cols))
  ) |>
  arrange(sampling_site_main_category)

p <- ggplot(site_summary, aes(x = 2, y = n, fill = sampling_site_main_category)) +
  geom_col(width = 1, color = "white", linewidth = 0.3) +
  coord_polar(theta = "y") +
  xlim(0.5, 2.5) +
  scale_fill_manual(values = site_cols, drop = FALSE) +
  labs(fill = "Sampling-site main category") +
  theme_void(base_size = 12) +
  theme(
    legend.position = "right",
    legend.title = element_text(size = 12),
    legend.text = element_text(size = 11)
  )

dir.create(dirname(outfile), showWarnings = FALSE, recursive = TRUE)

if (grepl("\\.svg$", outfile, ignore.case = TRUE) && requireNamespace("svglite", quietly = TRUE)) {
  ggsave(outfile, p, width = 10, height = 10, dpi = 300, device = svglite::svglite, bg = "white")
} else {
  ggsave(outfile, p, width = 10, height = 10, dpi = 300, bg = "white")
}

print(site_summary)
print(p)
