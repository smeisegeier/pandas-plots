# Install and load the ggsankey package if not already installed
# if (!require("ggsankey")) 
#install.packages("ggsankey")
#install.packages("ggplot2")
# library(ggsankey)

# # Create a simple dataset for the Sankey diagram
# # The data represents flows from one node to another with values
# data = data.frame(
#     source = c("A", "A", "B", "C"),
#     target = c("B", "C", "C", "D"),
#     value = c(10, 20, 30, 40)
# )

# # Plot the Sankey diagram using ggsankey
# ggplot(data, aes(x = source, xend = target, y = value, yend = value, fill = source)) +
#     geom_sankey(flow.alpha = 0.6, node.size = 10) +
#     geom_text(aes(
#         x = (as.numeric(source) + as.numeric(target)) / 2,
#         y = value, label = value
#     ), color = "black", size = 5, fontface = "bold") +
#     theme_void() +
#     ggtitle("Sankey Diagram with Numbers Visible")

# print("test")

cars <- mtcars
plot(cars)