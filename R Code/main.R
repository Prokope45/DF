cleaned_leases <- read.csv("/Users/prokope/Projects/DF/data/cleaned_leases.csv")

leases_lm <- lm(is_construction ~ Houston, data=cleaned_leases)
summary(leases_lm)
anova(leases_lm)
plot(cleaned_leases$is_construction, leases_lm$residuals, xlab = "Is Construction", ylab = "Residuals", main = "Plot of residuals against Construction", pch = 16)
