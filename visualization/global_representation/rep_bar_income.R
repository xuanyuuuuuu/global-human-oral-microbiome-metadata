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
  library(scales)
})

df <- read_csv(infile, show_col_types = FALSE)

if (!"log10_representation_proportion" %in% names(df)) {
  stop("log10_representation_proportion missing")
}

if (!"Group" %in% names(df)) {
  if ("Income_Group" %in% names(df)) {
    df <- df |> rename(Group = Income_Group)
  } else {
    stop("Group / Income_Group missing")
  }
}

df <- df |>
  mutate(
    Index_log = as.numeric(log10_representation_proportion),
    sign = ifelse(Index_log >= 0, "over", "under")
  ) |>
  arrange(desc(Index_log)) |>
  mutate(Group = factor(Group, levels = Group))

xlim_sym <- max(abs(df$Index_log), na.rm = TRUE) * 1.15
breaks_sym <- pretty(c(-xlim_sym, xlim_sym), n = 5)

p <- ggplot(df, aes(x = Index_log, y = Group, fill = sign)) +
  geom_col(width = 0.60) +
  geom_vline(xintercept = 0, linewidth = 0.4, colour = "grey30") +
  scale_y_discrete(expand = expansion(mult = c(0.2, 0.2))) +
  scale_fill_manual(values = c(under = "#92C5DE", over = "#F4A582")) +
  scale_x_continuous(
    limits = c(-xlim_sym, xlim_sym),
    breaks = breaks_sym,
    expand = expansion(mult = 0.02)
  ) +
  labs(
    x = expression(log[10]~"(Representation Index)"),
    y = NULL
  ) +
  theme_minimal(base_family = "sans") +
  theme(
    legend.position = "none",
    axis.text = element_text(size = 14, colour = "black"),
    axis.title.x = element_text(size = 15, margin = margin(t = 8)),
    panel.grid.major.y = element_line(linewidth = 0.3, colour = "grey85"),
    panel.grid.major.x = element_line(linewidth = 0.3, colour = "grey90"),
    plot.margin = margin(5, 55, 5, 20)
  ) +
  coord_cartesian(clip = "off")

dir.create(dirname(outfile), showWarnings = FALSE, recursive = TRUE)

if (grepl("\\.svg$", outfile, ignore.case = TRUE) && requireNamespace("svglite", quietly = TRUE)) {
  ggsave(outfile, p, width = 8, height = 4, device = svglite::svglite, bg = "white")
} else {
  ggsave(outfile, p, width = 8, height = 4, bg = "white")
}

print(p)
