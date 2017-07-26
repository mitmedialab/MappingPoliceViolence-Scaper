library(lubridate)
library(ggplot2)
require(MASS) # Contains glm.nb
library(gmodels) # Contains CrossTable
library(doBy)

# library(lme4)
# library(lmerTest)

rm(list=ls())

people <- read.csv("mentions-of-prior-incidents.csv")
people$date <- as.POSIXlt(people$date_of_death)
people$day.num <- as.integer(difftime(people$date, min(people$date), unit="days"))
brown.day.num <- subset(people, full_name=="Michael Brown")$day.num[[c(1)]]
people <- people[order(people$day.num), ]
people$id <- seq(1, nrow(people))
people <- subset(people, (day.num > brown.day.num) | (day.num < brown.day.num - 14))
people$after.brown <- people$day.num > brown.day.num


plot(people$day.num, people$stories_about_person)

plot(people$day.num, people$sentences_about_person)

plot(people$day.num, people$sentences_mentioning_prior_victims)

plot(people$day.num, log1p(people$sentences_mentioning_prior_victims))


##### CREATE PROPORTION OF OTHERS OVER STORIES
people$prop.others.over.stories <- 0

people$prop.others.over.stories[which(people$stories_about_person!=0)] <- 
  subset(people, stories_about_person!=0)$sentences_mentioning_prior_victims /
  subset(people, stories_about_person!=0)$stories_about_person

people$ln_sentences_of_other_victims <- log1p(people$sentences_mentioning_prior_victims)

plot(people$day.num, log1p(people$prop.others.over.stories))

ggplot(people, aes(day.num, sentences_mentioning_prior_victims, label=full_name)) +
  geom_label()

ggplot(people, aes(day.num, stories_about_person, label=full_name)) +
  geom_label()

ggplot(people, aes(day.num, prop.others.over.stories, label=full_name)) +
  geom_vline(xintercept=c(brown.day.num), linetype="dashed", size=1, color="gray") +
  geom_label()

ggplot(people, aes(day.num, prop.others.over.stories, label=full_name)) +
  geom_vline(xintercept=c(brown.day.num), linetype="dashed", size=1, color="gray") +
  geom_point()

plot(people$id, people$day.num)


summaryBy(ln_sentences_of_other_victims ~ after.brown, data=people, FUN=c(mean, min, max), na.rm=TRUE)
summaryBy(prop.others.over.stories ~ after.brown, data=people, FUN=c(mean, min, max), na.rm=TRUE)


###### SOME BASIC STATISTICAL MODELING ####
summary(others.nb1 <- glm.nb(sentences_mentioning_prior_victims ~  day.num + I(day.num^2), data=people))

##### PLOT MODEL
summary(others.nb1)

m=others.nb1
cat1 <-NULL
pf <-NULL
p<-NULL
p = data.frame(day.num = seq(min(people$day.num), max(people$day.num), 1))

p$id = max(people$id)
cat1 <-predict(m, newdata=p, type="link",conf.int=TRUE, se.fit=TRUE)

critval <- 1.96

pf <- p
pf$log_upr <- cat1$fit + (critval * cat1$se.fit)
pf$log_lwr <- cat1$fit - (critval * cat1$se.fit)
pf$log_others <- cat1$fit

pf$others <- m$family$linkinv(pf$log_others)
pf$upr2 <- m$family$linkinv(pf$log_upr)
pf$lwr2 <- m$family$linkinv(pf$log_upr)


### PLOT FULL VERSION
ggplot(pf, aes(x = day.num, y=others)) +
  geom_vline(xintercept=c(brown.day.num), linetype="dashed", size=1, color="gray") +
  geom_line(data=subset(pf, day.num<(brown.day.num-14)),size = 1) +
  geom_line(data=subset(pf, day.num>brown.day.num),size = 1) 
