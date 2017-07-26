library(ggplot2)
library(descr)
library(pander)
library(texreg)
require(MASS) # Contains glm.nb



rm(list=ls())

#################################
## LOAD PERSON DATASET         ##
#################################
people <- read.csv("mentions-of-prior-incidents.csv")
people.supplement <- read.csv("../data/people-dataset.csv")
people$name <- people$full_name
people <- merge(people, people.supplement, by = "name")
rm(people.supplement)

total.people <- nrow(people)

## DV of normalized.num.articles
people$normalized.stories <- round(people$normalized_num_articles_about_person*max(people$num_articles_in_mediacloud))

## NORMALIZED FACEBOOK SHARES PER PERSON
## people$normalized.social <- round((people$total_facebook_shares / people$num_articles_in_mediacloud)*max(people$num_articles_in_mediacloud))


## SET DATE INFORMATION FOR PERSON DATASET
people$date <- as.POSIXlt(people$date_of_death)
people$day.num <- as.integer(difftime(people$date, min(people$date), unit="days"))
brown.day.date <- subset(people, full_name=="Michael Brown")$date
brown.day.num <- subset(people, full_name=="Michael Brown")$day.num[[c(1)]]

strftime(max(people$date), "%b %d, %Y")

## ORDER PEOPLE BY DAY NUM AND REMOVE ANYONE WHO DIED IN THE 
## 14 DAYS BEFORE MICHAEL BROWN'S DEATH
people <- people[order(people$day.num), ]
people$id <- seq(1, nrow(people))
people <- subset(people, (day.num > brown.day.num) | (day.num < brown.day.num - 14))
people$after.brown <- as.integer(people$day.num > brown.day.num)

## 
people$prop.others.over.stories <- 0
people$prop.others.over.stories[which(people$stories_about_person!=0)] <- 
  subset(people, stories_about_person!=0)$sentences_mentioning_prior_victims /
  subset(people, stories_about_person!=0)$stories_about_person

## NUMBER OF SENTENCES IN ARTICLES ABOUT OTHER PEOPLE
people$ln.sentences.about.others <- log1p(people$sentences_mentioning_prior_victims)

## WHETHER THE ARTICLE INCLUDED AT LEAST ONE ARTICLE
people$any.articles <- people$normalized.stories > 0

## LOG OF POPULATION
people$ln.population <- log(people$population)

##########################################
## LOAD ARTICLE DATASET DATASET         ##
##########################################

stories <- read.csv("stories-with-of-prior-incidents.csv")

## FULL DESCRIPTION OF THIS DATASET
## One row for each article that appeared in the 14 days following someone's death
## and which mentioned that person.
## DUPLICATES are not included

## DATES & DATA CLEANING
stories$story.date <- as.Date(stories$story_date, format="%m/%d/%y")
stories$death.date <- as.Date(stories$date, format="%m/%d/%y")
stories$facebook.date <- as.Date(stories$facebook_api_collect_date, format="%m/%d/%y")

stories$death.day.num <- as.integer(stories$death.date - min(stories$story.date))
stories$story.day.since.death <- as.integer(stories$story.date - stories$death.date)
stories$story.day.num <- as.integer(stories$story.date - min(stories$story.date))

stories$facebook.delay.days <- as.integer(stories$facebook.date - stories$story.date)
stories$ln.population <- log1p(stories$population)

## FILTER OUT DUPLICATES
## IN A WAY THAT CHOOSES THE MOST RECENT DEATH
## BY SORTING ASCENDING BY story.day.num
stories <- with(stories, stories[order(stories_id, story.day.num),])
full.story.count <- nrow(stories)
stories <- stories[!duplicated(stories$stories_id), ]
stories.removed.dups <- full.story.count - nrow(stories)

## IDENTIFY THE DAY NUM OF MICHAEL BROWN'S DEATH
michael.brown.day.num <- unique(subset(stories, associated_name=="Michael Brown")$death.day.num)

## REMOVE MICHAEL BROWN
stories$after <- stories$death.day.num > michael.brown.day.num
stories$after.brown <- as.integer(stories$death.day.num > michael.brown.day.num)

stories <- subset(stories, associated_name!="Michael Brown")
stories.removed.michael.brown <- full.story.count - stories.removed.dups - nrow(stories)

## REMOVE STORIES FROM THE 15TH DAY OR OLDER
## (remember that the count starts at 0)
stories <- subset(stories, story.day.since.death < 14)
stories.removed.over.14.days <- full.story.count - stories.removed.dups - stories.removed.michael.brown - nrow(stories)

## CONSIDER WHETHER AT LEAST ONE OTHER VICTIM IS MENTIONED
stories$sentences.about.others <- stories$sentences_mentioning_prior_victims
stories$wider.issue <- stories$sentences_mentioning_prior_victims>0

##########################################
## SPECIFY NAMES TO INCLUDE IN LABELS   ##
##########################################
labelpeople <- subset(people, (name=="Eric Garner" | name=="Sandra Bland" | name=="Tamir E. Rice" |
                                 name=="Walter Scott" | name=="Akai Gurley" | name=="Ezell Ford" | 
                                 name=="Akiel Denkins" | name=="Cortez Washington" |
                                 name=="Dante Parker" | name=="Jessica Nelson-Williams" |
                                 name=="Corey Levert Tanner" | name=="Kionte Desean Spencer" |
                                 name=="Ashtain Barnes" | name=="Jonathan A. Ferrell" |
                                 name=="Jack Lamar Roberson" | name=="Warren Robinson" |
                                 name=="Dylan Samuel-Peters" | name=="Yvette Smith" |
                                 name=="Xavier Tyrell Johnson" | name=="Rumain Brisbon" | 
                                 name=="Clanesha Rayuna Shaqwanda Hickmon" | name=="Freddie Gray"))


###################################
## SUMMARY TABLES FOR PAPER      ##
###################################

pander(CrossTable(people$after.brown,people$any.articles,
           expected=FALSE, prop.r=TRUE, prop.c=FALSE,
           prop.t=FALSE, prop.chisq=FALSE, digits = 1))

pander(CrossTable(stories$after.brown,stories$wider.issue,
                  expected=FALSE, prop.r=TRUE, prop.c=FALSE,
                  prop.t=FALSE, prop.chisq=FALSE, digits = 1))

##########################################
## SUMMARY ILLUSTRATIONS FOR PAPER      ##
##########################################

###### VIOLIN PLOT OF NORMALIZED STORIES TO BEFORE/AFTER
ggplot(people, aes(factor(after.brown), log1p(normalized.stories), label = full_name, fill=factor(after.brown))) + 
  scale_fill_manual(name="Time Period", values=c("#999999", "#E95556"), 
                    labels=c("Before", "After")) +
  theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
        panel.background = element_blank(), axis.line.x = element_line(size=1, colour = "black"),
        axis.line.y = element_line(size=1, colour = "black"), axis.ticks = element_line(size=1),
        axis.ticks.length = unit(.15, "cm"), 
        axis.text=element_text(size=14),
        axis.title=element_text(size=18,face="bold"),
        legend.title = element_text(colour="black", size=18, face="bold"),
        legend.text = element_text(colour="black", size = 16)) +
  ylim(0,9) +
  ylab("ln Number of Stories") +
  scale_x_discrete("Time Period", labels = c("Before Michael Brown's Death","After Michael Brown's Death")) +
  geom_violin() +
  geom_jitter(width=0.5, shape=10, size=4, color="gray40") +
  geom_text(data=labelpeople, size=7)


###### JITTER PLOT OF NORMALIZED STORIES OVER TIME
ggplot(people, aes(x = day.num, y=log1p(normalized.stories))) +
  geom_vline(xintercept=c(brown.day.num), linetype="dashed", size=2, color="gray") +
  geom_point(data=subset(people, day.num<(brown.day.num-14)), aes(color="gray40"), shape=10, size=4) +
  geom_point(data=subset(people, day.num>brown.day.num), aes(color="red"), shape=10, size=4) +
  ylab("ln Number of Stories") +
  ylim(0,8) +
  scale_x_continuous(name ="",breaks=c(0,365,730,1095),
                     labels=c("2013", "2014", "2015", "2016")) +
  scale_colour_manual(name = 'Time Period', 
                      values =c('gray40'='gray40','red'='#E95556'), labels = c('Before','After')) +
  theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
        panel.background = element_blank(), axis.line.x = element_line(size=1, colour = "black"),
        axis.line.y = element_line(size=1, colour = "black"), axis.ticks = element_line(size=1),
        axis.ticks.length = unit(.15, "cm"), 
        axis.text=element_text(size=16),
        axis.title=element_text(size=18,face="bold"),
        legend.title = element_text(colour="black", size=18, face="bold"),
        legend.text = element_text(colour="black", size = 16))

###### JITTER PLOT OF OTHER PEOPLE MENTIONED, OVER TIME

ggplot(stories, aes(x = story.day.num, y=log1p(sentences.about.others))) +
  geom_vline(xintercept=c(brown.day.num), linetype="dashed", size=2, color="gray") +
  geom_point(data=subset(stories, story.day.num<(brown.day.num-14)), aes(color="gray40"), shape=10, size=4) +
  geom_point(data=subset(stories, story.day.num>brown.day.num), aes(color="red"), shape=10, size=4) +
  ylab("ln Sentences About Other Victims") +
  ylim(0,8) +
  scale_x_continuous(name ="",breaks=c(0,365,730,1095),
                     labels=c("2013", "2014", "2015", "2016")) +
  scale_colour_manual(name = 'Time Period', 
                      values =c('gray40'='gray40','red'='#E95556'), labels = c('Before','After')) +
  theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
        panel.background = element_blank(), axis.line.x = element_line(size=1, colour = "black"),
        axis.line.y = element_line(size=1, colour = "black"), axis.ticks = element_line(size=1),
        axis.ticks.length = unit(.15, "cm"), 
        axis.text=element_text(size=16),
        axis.title=element_text(size=18,face="bold"),
        legend.title = element_text(colour="black", size=18, face="bold"),
        legend.text = element_text(colour="black", size = 16))

##########################################
## STATISTICAL MODELS FOR PAPER         ##
##########################################

##########################################
### H1A: Change in chance of any article
##########################################

critval <- 1.96 ## approx 95% CI
summary(h1a <-glm(any.articles ~ age + gender + ln.population + after.brown, data=people, family=binomial(link="logit") ))
data.h1a <- data.frame(after.brown=c(0,1))
data.h1a$gender = "Male"
data.h1a$age = mean(people$age)
data.h1a$ln.population = log(median(people$population))
h1a.predictions <- predict(h1a, data.h1a, type="link", se.fit=TRUE)
data.h1a$upr <- h1a$family$linkinv(h1a.predictions$fit + (critval * h1a.predictions$se.fit))
data.h1a$lwr <- h1a$family$linkinv(h1a.predictions$fit - (critval * h1a.predictions$se.fit))
data.h1a$dv  <- h1a$family$linkinv(h1a.predictions$fit)

ggplot(data.h1a, aes(factor(after.brown), dv)) +
  geom_bar(stat="identity", fill='gray90') +
  ylab("Fitted Probability of Having 1+ Stories") +
  scale_y_continuous(labels = scales::percent) +
  geom_text(aes(label=sprintf("%1.2f%%", 100*dv)), vjust=1.5, #hjust=0.7, 
            size=7, color="gray40", fontface="bold") +
  scale_x_discrete("", labels = c("Before Michael Brown's Death","After Michael Brown's Death")) +
  geom_errorbar(aes(ymin = lwr, ymax = upr), width=0.1) +
  theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
        panel.background = element_blank(), axis.line.x = element_line(size=1, colour = "black"),
        axis.line.y = element_line(size=1, colour = "black"), axis.ticks = element_line(size=1),
        axis.ticks.length = unit(.15, "cm"), 
        axis.text=element_text(size=16),
        axis.title=element_text(size=18,face="bold"),
        legend.title = element_text(colour="black", size=18, face="bold"),
        legend.text = element_text(colour="black", size = 16))

screenreg(h1a, digits=3, label="table:comment.effect", 
          custom.model.names=c("Logistic Regression"),
          custom.coef.names = c("Intercept", "Age", 
                                "Gender (Male)","ln Population", "After Brown's Death"),
          caption="In the period after Michael Brown's death, an unarmed black person killed by the police had a 24.9 percentage point greater chance of having at least one article written about them.")

##########################################
### H1B: Change in incidence rate of articles
##########################################
summary(h1b.base <- glm.nb(normalized.stories ~ 1, data=people))

summary(h1b.model <- glm.nb(normalized.stories ~ age + gender + ln.population + 
                                  day.num + I(day.num^2) + I(day.num^3), data=people))


data.h1b = data.frame(day.num = seq(min(people$day.num), max(people$day.num), 1))

data.h1b$age = mean(people$age)
data.h1b$gender = "Male"
data.h1b$ln.population = log1p(median(people$population))
h1b.predictions <- predict(h1b.model, newdata=data.h1b, type="link",conf.int=TRUE, se.fit=TRUE)
data.h1b$log_upr <- h1b.predictions$fit + (critval * h1b.predictions$se.fit)
data.h1b$log_lwr <- h1b.predictions$fit - (critval * h1b.predictions$se.fit)
data.h1b$dv  <- h1b.model$family$linkinv(h1b.predictions$fit)
data.h1b$upr <- h1b.model$family$linkinv(data.h1b$log_upr)
data.h1b$lwr <- h1b.model$family$linkinv(data.h1b$log_lwr)


### PLOT FULL VERSION
ggplot(data.h1b, aes(x = day.num, y=dv)) +
  geom_vline(xintercept=c(brown.day.num), linetype="dashed", size=1, color="gray") +
  geom_line(data=subset(data.h1b, day.num<(brown.day.num-14)),size = 1, aes(color="gray40")) +
  geom_line(data=subset(data.h1b, day.num>brown.day.num),size = 1, aes(color="red")) +
  geom_ribbon(aes(ymin=data.h1b$lwr, ymax=data.h1b$upr), alpha=0.1) +
  #  geom_point(data=people,aes(x=people$day.num, y=people$num_articles), alpha=.9, position=position_jitter(h=.2), color="red") +
  #  geom_text(data=people,aes(label=name), size=3, alpha=0.8) + 
  #  geom_vline(xintercept=c(221,235), linetype="dotted") +
  ylab("Incidence Rate of Stories") +
  ylim(0,160) +
  scale_x_continuous(name ="",breaks=c(0,365,730,1095),
                     labels=c("2013", "2014", "2015", "2016")) +
  scale_colour_manual(name = 'Time Period', 
                      values =c('gray40'='gray40','red'='#E95556'), labels = c('Before','After')) +
  theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
        panel.background = element_blank(), axis.line.x = element_line(size=1, colour = "black"),
        axis.line.y = element_line(size=1, colour = "black"), axis.ticks = element_line(size=1),
        axis.ticks.length = unit(.15, "cm"), 
        axis.text=element_text(size=16),
        axis.title=element_text(size=18,face="bold"),
        legend.title = element_text(colour="black", size=18, face="bold"),
        legend.text = element_text(colour="black", size = 16))

## TABLE OUTPUT
data.h1b.max.fitted.day <- subset(data.h1b, dv==max(data.h1b$dv))$day.num
screenreg(h1b.model, digits=8, label="table:comment.effect", 
          custom.model.names=c("Modeling The Number of Stories"),
          custom.coef.names = c("Intercept", "Age", 
                                "Gender (Male)","ln Population", "Day Number", "Day Number^2", "Day Number^3"),
          caption=paste("The incidence rate of stories grew up to",data.h1b.max.fitted.day,"days after Michael Brown's death on average, and then declined."))

library(stargazer)
stargazer(h1b.model, type="html")
##############################################################
### H2A: Change in chance of story to mention other people  ##
##############################################################
summary(h2a <-glm(wider.issue ~ age + gender + ln.population + after.brown, data=stories, family=binomial(link="logit") ))


data.h2a <- data.frame(after.brown=c(0,1))
data.h2a$gender = "Male"
data.h2a$age = mean(people$age) # USE PEOPLE HERE 
data.h2a$ln.population = log(median(people$population)) # USE PEOPLE HERE 
h2a.predictions <- predict(h2a, data.h2a, type="link", se.fit=TRUE)
data.h2a$upr <- h1a$family$linkinv(h2a.predictions$fit + (critval * h2a.predictions$se.fit))
data.h2a$lwr <- h1a$family$linkinv(h2a.predictions$fit - (critval * h2a.predictions$se.fit))
data.h2a$dv  <- h1a$family$linkinv(h2a.predictions$fit)

ggplot(data.h2a, aes(factor(after.brown), dv)) +
  geom_bar(stat="identity", fill='gray90') +
  ylab("Fitted Probability of Including 1+ Others") +
  scale_y_continuous(labels = scales::percent) +
  geom_text(aes(label=sprintf("%1.2f%%", 100*dv)), vjust=1.5, hjust=1.4, 
            size=7, color="gray40", fontface="bold") +
  scale_x_discrete("", labels = c("Before Michael Brown's Death","After Michael Brown's Death")) +
  geom_errorbar(aes(ymin = lwr, ymax = upr), width=0.1) +
  theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
        panel.background = element_blank(), axis.line.x = element_line(size=1, colour = "black"),
        axis.line.y = element_line(size=1, colour = "black"), axis.ticks = element_line(size=1),
        axis.ticks.length = unit(.15, "cm"), 
        axis.text=element_text(size=16),
        axis.title=element_text(size=18,face="bold"),
        legend.title = element_text(colour="black", size=18, face="bold"),
        legend.text = element_text(colour="black", size = 16))

screenreg(h2a, digits=3, label="table:comment.effect", 
          custom.model.names=c("Logistic Regression"),
          custom.coef.names = c("Intercept", "Age", 
                                "Gender (Male)","ln Population", "After Brown's Death"),
          caption="In the period after Michael Brown's death, a story about an unarmed black person killed by the police had a18.27 percentage point greater chance of including a mention of at least one other victim, on average")

##########################################################################
### H2B: Change in incidence rate of sentences mentioning other people  ##
##########################################################################

summary(h2b.model <- glm.nb(sentences_mentioning_prior_victims ~ gender + ln.population + death.day.num + I(death.day.num^2) + after.brown + after.brown:death.day.num, data=stories))
summary(h2b.model <- glm.nb(sentences_mentioning_prior_victims ~ gender + ln.population + death.day.num + I(death.day.num^2) + I(death.day.num^3), data=stories))


data.h2b = data.frame(death.day.num = seq(min(people$day.num), max(people$day.num), 1))
data.h2b$after.brown <- as.integer(data.h2b$death.day.num > michael.brown.day.num)
data.h2b$age = mean(people$age)
data.h2b$gender = "Male"
data.h2b$ln.population = log1p(median(people$population))
h2b.predictions <- predict(h2b.model, newdata=data.h2b, type="link",conf.int=TRUE, se.fit=TRUE)
data.h2b$log_upr <- h2b.predictions$fit + (critval * h2b.predictions$se.fit)
data.h2b$log_lwr <- h2b.predictions$fit - (critval * h2b.predictions$se.fit)
data.h2b$dv  <- h2b.model$family$linkinv(h2b.predictions$fit)
data.h2b$upr <- h2b.model$family$linkinv(data.h2b$log_upr)
data.h2b$lwr <- h2b.model$family$linkinv(data.h2b$log_lwr)



ggplot(data.h2b, aes(x = death.day.num, y=dv)) +
  geom_vline(xintercept=c(brown.day.num), linetype="dashed", size=1, color="gray") +
  geom_line(data=subset(data.h2b, death.day.num<(brown.day.num-14)),size = 1, aes(color="gray40")) +
  geom_line(data=subset(data.h2b, death.day.num>brown.day.num),size = 1, aes(color="red")) +
  geom_ribbon(aes(ymin=data.h2b$lwr, ymax=data.h2b$upr), alpha=0.1) +
  #  geom_point(data=people,aes(x=people$day.num, y=people$num_articles), alpha=.9, position=position_jitter(h=.2), color="red") +
  #  geom_text(data=people,aes(label=name), size=3, alpha=0.8) + 
  #  geom_vline(xintercept=c(221,235), linetype="dotted") +
  ylab("Incidence Rate of Mentions") +
#  ylim(0,160) +
  scale_x_continuous(name ="",breaks=c(0,365,730,1095),
                     labels=c("2013", "2014", "2015", "2016")) +
  scale_colour_manual(name = 'Time Period', 
                      values =c('gray40'='gray40','red'='#E95556'), labels = c('Before','After')) +
  theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
        panel.background = element_blank(), axis.line.x = element_line(size=1, colour = "black"),
        axis.line.y = element_line(size=1, colour = "black"), axis.ticks = element_line(size=1),
        axis.ticks.length = unit(.15, "cm"), 
        axis.text=element_text(size=16),
        axis.title=element_text(size=18,face="bold"),
        legend.title = element_text(colour="black", size=18, face="bold"),
        legend.text = element_text(colour="black", size = 16))


##########################################
## SAVE IMAGE FOR R MARDKOWN OUTPUT     ##
##########################################
save.image("full-analysis-BLM-paper.RData")


  