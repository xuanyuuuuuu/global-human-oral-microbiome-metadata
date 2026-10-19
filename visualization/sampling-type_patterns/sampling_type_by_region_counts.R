# ============================================
# Figure 1G: Sampling-type counts by SDG region
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

bios_path    <- get_arg("--biosample")
country_path <- get_arg("--country")
outfile      <- get_arg("--out")

if (is.null(bios_path) || is.null(country_path) || is.null(outfile)) {
  stop(
    "Usage: Rscript figure1G_sampling_type_by_region_counts.R ",
    "--biosample final_biosample.csv ",
    "--country country_population_group.csv ",
    "--out figure1G_sampling_type_by_region_counts.svg"
  )
}

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
  library(scales)
})

bios <- read_csv(bios_path, show_col_types = FALSE)
country_info <- read_csv(country_path, show_col_types = FALSE)

# ----------------------------
# 检查列
# ----------------------------
if (!"country_clean" %in% names(bios)) stop("country_clean missing")
if (!"sampling_type_main_category" %in% names(bios)) stop("sampling_type_main_category missing")
if (!"country_clean" %in% names(country_info)) stop("country_clean missing in country")
if (!"SDG_Region" %in% names(country_info)) stop("SDG_Region missing in country")

# ----------------------------
# 数据清洗
# ----------------------------
bios_clean <- bios %>%
  mutate(
    country_clean = trimws(as.character(country_clean)),
    sampling_type_main_category = trimws(as.character(sampling_type_main_category))
  ) %>%
  filter(
    !is.na(country_clean),
    country_clean != "Unknown",
    !is.na(sampling_type_main_category),
    !sampling_type_main_category %in% c("Unspecified", "Unknown")
  )

country_sdg <- country_info %>%
  select(country_clean, SDG_Region) %>%
  mutate(
    country_clean = trimws(as.character(country_clean)),
    SDG_Region = trimws(as.character(SDG_Region))
  )

df_joined <- bios_clean %>%
  left_join(country_sdg, by = "country_clean") %>%
  filter(
    !is.na(SDG_Region),
    !SDG_Region %in% c("Unreported", "(Unreported)")
  )

# ----------------------------
# 颜色
# ----------------------------
type_cols <- c(
  "Oral Fluids" = "#F4A7A0",
  "Dental Plaque and Calculus" = "#4C72B0",
  "Oral Mucosa and Surfaces" = "#A5BDE0",
  "Special/Lesion Sites" = "#B3A3C9"
)

# ----------------------------
# 统计
# ----------------------------
plot_df <- df_joined %>%
  count(SDG_Region, sampling_type_main_category, name = "n")

# ----------------------------
# 排序（按总样本）
# ----------------------------
sdg_order <- plot_df %>%
  group_by(SDG_Region) %>%
  summarise(total = sum(n), .groups = "drop") %>%
  arrange(desc(total)) %>%
  pull(SDG_Region)

plot_df <- plot_df %>%
  mutate(
    SDG_Region = factor(SDG_Region, levels = rev(sdg_order)),
    sampling_type_main_category = factor(
      sampling_type_main_category,
      levels = names(type_cols)
    )
  )

# ----------------------------
# 计算最大值（统一 x 轴）
# ----------------------------
max_total <- plot_df %>%
  group_by(SDG_Region) %>%
  summarise(total = sum(n), .groups = "drop") %>%
  pull(total) %>%
  max(na.rm = TRUE)

# ----------------------------
# 画图
# ----------------------------
p <- ggplot(
  plot_df,
  aes(x = n, y = SDG_Region, fill = sampling_type_main_category)
) +
  geom_col(width = 0.7) +
  scale_x_continuous(
    limits = c(0, max_total),
    labels = comma_format(accuracy = 1),
    expand = expansion(mult = c(0, 0.01))
  ) +
  scale_fill_manual(values = type_cols, drop = FALSE) +
  labs(
    x = "Total samples",
    y = "SDG region",
    fill = "Sampling-type main category"
  ) +
  theme_bw(base_size = 12) +
  theme(
    panel.grid.major.y = element_blank(),
    panel.grid.minor = element_blank()
  )

# ----------------------------
# 保存
# ----------------------------
dir.create(dirname(outfile), showWarnings = FALSE, recursive = TRUE)

if (grepl("\\.svg$", outfile, ignore.case = TRUE) &&
    requireNamespace("svglite", quietly = TRUE)) {
  ggsave(outfile, p, width = 6.5, height = 4.5, dpi = 300,
         device = svglite::svglite, bg = "white")
} else {
  ggsave(outfile, p, width = 6.5, height = 4.5, dpi = 300, bg = "white")
}

print(p)