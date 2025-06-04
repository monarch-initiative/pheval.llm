library(ggplot2)
library(dplyr)
library(tidyr)
library(ggsci)  # For Lancet/Nature color palettes

mode <- "manual"
# Use switch to assign the file path
tsv_file <- switch(mode,
                   gpt = "/Users/leonardo/git/malco/final_multilingual_output/rank_data/topn_result.tsv",
                   #gpt = "/Users/leonardo/git/malco/allmeditron.tsv",
                   manual = "/Users/leonardo/git/malco/out_manual_curation/multilingual/rank_data/curated_topn_result.tsv",
                   stop("Unknown mode")  # fallback if mode doesn't match
)
# case Meditron necessary?

# Data
data <- read.delim(tsv_file, header = TRUE, sep = "\t", stringsAsFactors = FALSE)

# Process and normalize data
data <- data %>%
  rename(Lang = language) %>%
  mutate(
    Top1 = n1,
    Top3 = n1 + n2 + n3,
    Top10 = n1 + n2 + n3 + n4 + n5 + n6 + n7 + n8 + n9 + n10,
    #NotRanked = grounding_failed + nf,
    NotRanked = nf,
    Total = Top10 + NotRanked,
    Top1 = Top1 / Total,
    Top3 = Top3 / Total,
    Top10 = Top10 / Total
  ) %>%
  select(Lang, Top1, Top3, Top10) # Keep only necessary columns

# Transform the data into long format
data_long <- data %>%
  pivot_longer(cols = Top1:Top10, names_to = "Rank", values_to = "Proportion")

data_long$Lang <- switch(mode,
                         # Reorder Lang: Put "en" first, followed by others alphabetically (!)
                         gpt = factor(data_long$Lang, levels = c("en", sort(setdiff(unique(data_long$Lang), "en")))),
                         manual = factor(data_long$Lang),
                         stop("Unknown mode")  # fallback if mode doesn't match
                         )

# Order the Rank levels
data_long$Rank <- factor(data_long$Rank, levels = c("Top1", "Top3", "Top10"))

# Define a custom subdued color palette

color_palette <- switch(mode,
                        gpt = c("en" = "#1B4F72","ja" = "#AAB7B8", "it" = "#D5DBDB", "cs" = "#A9CCE3", "tr" = "#F9E79F",
                                "nl" = "#85C1E9","de" = "#5499C7", "es" = "#5D6D7E", "zh" = "#D7BDE2", "fr" = "#F5CBA7"),
                        manual = c( "de_no_en" = "#A9CCE3","de_w_en" = "#D5DBDB", "es_no_en" = "#5499C7", "es_w_en" = "#85C1E9",
                                    "it_no_en" = "#AAB7B8","it_w_en" = "#1B4F72"),
                        stop("Unknown mode") )

full_names <- switch(mode, # alphabetically ordered, according to two-letter language code (!)
                     gpt = c("English", "Czech","German", "Spanish","French", "Italian","Japanese","Dutch","Turkish","Chinese"),
                     manual = c("German Reply", "German, EN Reply","Spanish Reply", "Spanish, EN Reply", "Italian Reply","Italian, EN Reply"),
                     stop("unknown mode") )

# Plot
#switch
#case gpt
upper_y_axis = 0.40
# case manual curation
upper_y_axis = 0.50

p <- ggplot(data_long, aes(x = Rank, y = Proportion, fill = Lang)) + #ylim(0,62) +
  geom_bar(stat = "identity", position = "dodge", color = "black", size = 0.3) +  # Black border, thin
  scale_fill_manual(values = color_palette, labels=full_names) +  # Professional color palette
  labs(
    #title = "Ranks Across Languages",
    y = "%",
    fill = "Language"
  ) +
  theme_classic(base_size = 14) +  # Journal-style theme
  scale_y_continuous(limits = c(0, upper_y_axis),
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
  coord_fixed(ratio=4)

#pdf()
ggsave(
  filename = "/Users/leonardo/Desktop/papers/multlingualGPT/plots_figures/supplemental_figure_s1.pdf",  # output filename
  plot = p,                  # plot object
  width = 10,                 # width in inches
  height = 7,                # height in inches
  units = "in"               # can be "in", "cm", or "mm"
)

