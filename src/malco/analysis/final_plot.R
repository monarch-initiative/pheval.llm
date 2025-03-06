library(ggplot2)
library(dplyr)
library(tidyr)
library(ggsci)  # For Lancet/Nature color palettes

# Data
data <- data.frame(
  Lang = c("ja", "it", "cs", "zh", "nl", "de", "es", "en", "tr"),
  Top1 = c(796, 860, 887, 917, 1013, 944, 951, 985, 903),
  Top3 = c(1256, 1327, 1252, 1352, 1370, 1304, 1370, 1340, 1311),
  Top10 = c(1364, 1514, 1409, 1417, 1521, 1455, 1579, 1546, 1449),
  NotRanked = c(3348, 3450, 3532, 3544, 3423, 3411, 3388, 3420, 3473)
)

# Normalize Top1, Top3, Top10 by (Top10 + NotRanked)
data <- data %>%
  mutate(
    Total = Top10 + NotRanked,
    Top1 = Top1 / Total,# * 100,
    Top3 = Top3 / Total,# * 100,
    Top10 = Top10 / Total,#  * 100
  ) %>%
  select(-NotRanked, -Total)

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

