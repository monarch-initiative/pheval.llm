library(ggplot2)
library(dplyr)
library(tidyr)
library(ggsci)  # For Lancet/Nature color palettes


tsv_file <- "/Users/leonardo/git/malco/leakage_experiment/rank_data/topn_result.tsv"

# Data
data <- read.delim(tsv_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)

# Process and normalize data
data <- data %>%
  rename(Lang = language) %>%
  mutate(
    Top1 = n1,
    Top3 = n1 + n2 + n3,
    Top10 = n1 + n2 + n3 + n4 + n5 + n6 + n7 + n8 + n9 + n10,
    NotRanked = grounding_failed + nf,
    Total = Top10 + NotRanked,
    Top1 = Top1 / Total,
    Top3 = Top3 / Total,
    Top10 = Top10 / Total
  ) %>%
  select(Lang, Top1, Top3, Top10) # Keep only necessary columns

# Transform the data into long format
data_long <- data %>%
  pivot_longer(cols = Top1:Top10, names_to = "Rank", values_to = "Proportion")

# Reorder Lang: Put "en" first, followed by others alphabetically
data_long$Lang <- factor(data_long$Lang, levels = c("en", sort(setdiff(unique(data_long$Lang), "en"))))

# Order the Rank levels
data_long$Rank <- factor(data_long$Rank, levels = c("Top1", "Top3", "Top10"))

# Define a custom subdued color palette
color_palette <- c(
  "en" = "#1B4F72",  # Deep Blue for English
  "ja" = "#AAB7B8", "it" = "#D5DBDB", "cs" = "#A9CCE3", "zh" = "#F9E79F",
  "nl" = "#85C1E9", "de" = "#5499C7", "es" = "#5D6D7E", "tr" = "#D7BDE2"
)

full_names = c("English", "Czech","German", "Spanish","Italian","Japanese","Dutch","Turkish","Chinese")
  

# Plot
ggplot(data_long, aes(x = Rank, y = Proportion, fill = Lang)) + #ylim(0,62) +
  geom_bar(stat = "identity", position = "dodge", color = "black", size = 0.3) +  # Black border, thin
  scale_fill_manual(values = color_palette, labels=full_names) +  # Professional color palette
  labs(
    title = "Ranks Across Languages (English Highlighted)",
    y = "%",
    fill = "Language"
  ) +
  theme_classic(base_size = 14) +  # Journal-style theme
  scale_y_continuous(limits = c(0, 0.4),
                     labels = scales::percent_format(accuracy = 1)) +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1, size = 15),
    axis.text.y = element_text(size = 15),
    #axis.title = element_text(size = 14, face = "bold"),
    axis.title = element_blank(),
    legend.title = element_text(face = "bold", size = 15),
    legend.text = element_text(size = 14),
    legend.position = "right",
    panel.grid.major.y = element_line(color = "#AAB7B8", linetype = "dashed")  # Subtle horizontal grid lines
  )+
  coord_fixed(ratio=5)

