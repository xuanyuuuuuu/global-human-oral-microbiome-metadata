# ============================================
# Figure 1E: Sampling-type composition
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

infile <- get_arg("--input")
outfile <- get_arg("--out")

if (is.null(infile) || is.null(outfile)) {
  stop(
    paste(
      "Usage:",
      "Rscript figure1E_sampling_type_pie.R",
      "--input final_biosample.csv",
      "--out figure1E_sampling_type_pie.svg"
    )
  )
}

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
})

bios <- read_csv(infile, show_col_types = FALSE)

if (!"sampling_type_main_category" %in% names(bios)) {
  stop("sampling_type_main_category missing")
}

df <- bios |>
  mutate(
    sampling_type_main_category = trimws(as.character(sampling_type_main_category))
  ) |>
  filter(
    !is.na(sampling_type_main_category),
    !sampling_type_main_category %in% c("Unspecified", "Unknown")
  )

type_cols <- c(
  "Oral Fluids" = "#F4A7A0",
  "Dental Plaque and Calculus" = "#4C72B0",
  "Oral Mucosa and Surfaces" = "#A5BDE0",
  "Special/Lesion Sites" = "#B3A3C9"
)

type_summary <- df |>
  count(sampling_type_main_category, name = "n") |>
  mutate(
    sampling_type_main_category = factor(
      sampling_type_main_category,
      levels = names(type_cols)
    )
  ) |>
  arrange(sampling_type_main_category)

p <- ggplot(type_summary, aes(x = 2, y = n, fill = sampling_type_main_category)) +
  geom_col(width = 1, color = "white", linewidth = 0.3) +
  coord_polar(theta = "y") +
  xlim(0.5, 2.5) +
  scale_fill_manual(values = type_cols, drop = FALSE) +
  labs(fill = "Sampling-type main category") +
  theme_void(base_size = 12) +
  theme(
    legend.position = "right",
    legend.title = element_text(size = 12),
    legend.text = element_text(size = 11)
  )

dir.create(dirname(outfile), showWarnings = FALSE, recursive = TRUE)

if (grepl("\\.svg$", outfile, ignore.case = TRUE) &&
    requireNamespace("svglite", quietly = TRUE)) {
  ggsave(outfile, p, width = 10, height = 10, dpi = 300,
         device = svglite::svglite, bg = "white")
} else {
  ggsave(outfile, p, width = 10, height = 10, dpi = 300, bg = "white")
}

print(type_summary)
print(p)