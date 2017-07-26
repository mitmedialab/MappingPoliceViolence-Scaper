#install.packages('corrplot')
library(ggplot2)
library(lattice)
library(corrplot)
library(AER)
library(MASS)
library(foreign)
library(lme4)
library(lmerTest)
require(pscl)
require(boot)
library(gmodels)
library(stargazer)
library(car)

rm(list=ls())
stories <- read.csv("stories-with-of-prior-incidents.csv")

## FULL DESCRIPTION OF THIS DATASET
## One row for each article that appeared in the 14 days following someone's death
## and which mentioned that person. 
## (TODO: decide if you want to remove duplicates. For the framing question, I think I do)

### TASK LIST:
# FOR FRAMING ANALYSIS:
## 1. Remove duplicate stories
## 2. Illustrate Number of sentences over time
## 3. Do non-LMER negative binomial to get the curve
## 4. Illustrate the NB with a chart
## 5. Do the LMER logistic regression to confirm the pattern
## 6. Look at the trend within an article

### DATA CLEANING & FIELDS
stories$story.date <- as.Date(stories$story_date, format="%m/%d/%y")
stories$death.date <- as.Date(stories$date, format="%m/%d/%y")
stories$facebook.date <- as.Date(stories$facebook_api_collect_date, format="%m/%d/%y")

stories$death.day.num <- as.integer(stories$death.date - min(stories$story.date))
stories$story.day.since.death <- as.integer(stories$story.date - stories$death.date)
stories$story.day.num <- as.integer(stories$story.date - min(stories$story.date))

stories$facebook.delay.days <- as.integer(stories$facebook.date - stories$story.date)
stories$log.population <- log1p(stories$population)
stories$person.story.id <- paste(stories$stories_id, stories$associated_name)

### FILTER OUT DUPLICATES
### IN A WAY THAT CHOOSES THE MOST RECENT DEATH
### BY SORTING ASCENDING BY story.day.num
stories <- with(stories, stories[order(stories_id, story.day.num),])
full.story.count <- nrow(stories)
stories <- stories[!duplicated(stories$stories_id), ]
stories.removed.dups <- full.story.count - nrow(stories)

max(stories$death.day.num)
max(stories$death.date)

### ADD IN BEFORE/AFTER MICHAEL BROWN

michael.brown.day.num <- unique(subset(stories, associated_name=="Michael Brown")$death.day.num)

## REMOVE MICHAEL BROWN
stories$after <- stories$death.day.num > michael.brown.day.num
stories <- subset(stories, associated_name!="Michael Brown")
stories.removed.michael.brown <- full.story.count - stories.removed.dups - nrow(stories)

## REMOVE STORIES FROM THE 14TH DAY OR OLDER
nrow(stories)
stories <- subset(stories, story.day.since.death < 14)
stories.removed.over.14.days <- full.story.count - stories.removed.dups - stories.removed.michael.brown - nrow(stories)

### CHECK FOR DUPLICATE STORIES, WHICH SHOULDN'T EXIST
pct.overlap <- length(unique(stories$stories_id)) / length(stories$stories_id)
pct.overlap
length(unique(stories$person.story.id)) / length(stories$stories_id)

### CONSIDER WHETHER AT LEAST ONE OTHER VICTIM IS MENTIONED
stories$wider.issue <- stories$sentences_mentioning_prior_victims>0

### UNIVARIATE STATISTICS
min(stories$story.date)

max(stories$story.date)

summary(stories$facebook_share_count)

summary(stories$facebook.delay.days)

hist(stories$facebook.delay.days)

summary(stories$wider.issue)
summary(stories$sentences_mentioning_prior_victims)
summary(stories$num_sentences)

hist(log1p(stories$sentences_mentioning_prior_victims))

summary(stories$story.day.since.death)
hist(stories$story.day.since.death)

summary(stories$age)
summary(stories$gender)
hist(log1p(stories$population))

##########################
### BIVARIATE STATISTICS

### SENTENCES MENTIONING PRIOR VICTIMES BY DAY NUM
ggplot(stories, aes(death.day.num, sentences_mentioning_prior_victims)) +
  geom_jitter()

### VICTIM GENDER
ggplot(stories, aes(gender, sentences_mentioning_prior_victims, color=gender)) +
  geom_jitter()

### INCIDENT REGION POPULATION
ggplot(stories, aes(log1p(population), sentences_mentioning_prior_victims, color=gender)) +
  geom_jitter()

### AFTER MICHAEL BROWN
ggplot(stories, aes(after, sentences_mentioning_prior_victims, color=factor(after))) +
  geom_jitter()

##########################################################
CrossTable(stories$after, stories$wider.issue,  
           prop.r=TRUE, prop.c=FALSE, prop.t=FALSE, prop.chisq=FALSE, chisq = TRUE)
##########################################################

### SENTENCES MENTIONING PRIOR VICTIMES BY DAY SINCE DEATH
ggplot(stories, aes(factor(story.day.since.death), sentences_mentioning_prior_victims, color=gender)) +
  geom_jitter() +
  facet_grid(after ~ . )

### FACEBOOK SHARES FOR ARTICLES USING THE SYSTEMIC ISSUE FRAME
ggplot(stories, aes(factor(floor(story.day.num / 7)), log1p(facebook_share_count))) +
  geom_violin()

ggplot(stories, aes(factor(after), log1p(facebook_share_count))) +
  geom_violin()

ggplot(stories, aes(factor(after), facebook_share_count)) +
  geom_violin()


### NOW VIEW A FACET GRID OF A SUBSET OF SENTENCES MENTIONING PRIOR VICTIMS BY DAY SINCE DEATH
stories.subset <- stories[which(stories$associated_name %in% sample(unique(stories$associated_name),10)),]

ggplot(stories.subset, aes(story.day.since.death, sentences_mentioning_prior_victims)) +
  geom_jitter() + 
  facet_grid(associated_name ~ .) +
  theme(axis.title.x=element_blank(),
        axis.text.x=element_blank(),
        axis.ticks.x=element_blank())

##########################################
### COUNT MODELING

### TEST INDIVIDUAL HYPOTHESES

summary(glm.nb(sentences_mentioning_prior_victims ~ after, data=stories))

summary(glm.nb(sentences_mentioning_prior_victims ~ gender, data=stories))

summary(glm.nb(sentences_mentioning_prior_victims ~ gender + log1p(population), data=stories))

summary(glm.nb(sentences_mentioning_prior_victims ~ gender + log1p(population) + after, data=stories))

summary(glm.nb(sentences_mentioning_prior_victims ~ gender + log1p(population) + after + death.day.num + I(death.day.num^2), data=stories))

summary(glm.nb(sentences_mentioning_prior_victims ~ gender + log1p(population) + death.day.num + I(death.day.num^2), data=stories))

summary(nb0 <- glm.nb(sentences_mentioning_prior_victims ~1, data=stories))

stories$log.num.sentences <- log1p(stories$num_sentences)
summary(nb1 <- glm.nb(sentences_mentioning_prior_victims ~ gender + age + log.population + after + story.day.num + log.num.sentences, data=stories))
#summary(nber1 <- glmer.nb(sentences_mentioning_prior_victims ~ gender + age + log.population + after + story.day.num + log.num.sentences + (1|stories_id), data=stories))
rm(nber1)
################ VISUALIZE NEGATIVE BINOMIAL MODEL ################ 
m=nb1
cat1 <-NULL
pf <-NULL
p<-NULL
p = data.frame(story.day.num = seq(min(stories$story.day.num), max(stories$story.day.num), 1))
p$after <- p$story.day.num > michael.brown.day.num
p$gender= "Male"
p$age = median(stories$age)
p$log.population = log1p(median(stories$population))
p$log.num.sentences = log1p(median(stories$num_sentences))
cat1 <-predict(m, newdata=p, type="link",conf.int=TRUE, se.fit=TRUE)
critval <- 1.96

pf <- p
pf$log_upr <- cat1$fit + (critval * cat1$se.fit)
pf$log_lwr <- cat1$fit - (critval * cat1$se.fit)
pf$log.dv <- cat1$fit

pf$dv <- m$family$linkinv(pf$log.dv)
pf$upr2 <- m$family$linkinv(pf$log_upr)
pf$lwr2 <- m$family$linkinv(pf$log_lwr)

### PLOT FULL VERSION
ggplot(pf, aes(x = story.day.num, y=dv)) +
  geom_point(data=stories,aes(x=stories$death.day.num, y=stories$sentences_mentioning_prior_victims), alpha=.2, position=position_jitter(h=.2,w=0.2)) +
  geom_line(data=subset(pf, after==FALSE),size = 1, color="red") +
  geom_line(data=subset(pf, after==TRUE),size = 1, color="red") +
  geom_ribbon(aes(ymin=pf$lwr2, ymax=pf$upr2), alpha=0.1) +
  geom_vline(xintercept=c(michael.brown.day.num), linetype="dotted") +
  ggtitle("Predicted Incidence Rate of Other People Mentioned, by Story Date")

## PLOT LOGGED VERSION
# ggplot(pf, aes(x = story.day.num, y=log.dv)) +
#   geom_line(data=pf,size = 1, color="red") +
#   geom_ribbon(aes(ymin=pf$log_lwr, ymax=pf$log_upr), alpha=0.1) +
#   geom_vline(xintercept=c(michael.brown.day.num), linetype="dotted") +
#   ggtitle("Predicted Articles Per Black Person Killed By The Police or who Died in Police Custody 2014, by Death Date")


##########################################
### LONGITUDINAL HYPOTHESIS
# 
# summary(glmer.nb(sentences_mentioning_prior_victims ~ death.day.num + (1|associated_name), data=stories))
# 
# summary(glmer.nb(sentences_mentioning_prior_victims ~ death.day.num + gender + log1p(population) + (1|associated_name), data=stories))
# 
# summary(rinb1 <- glmer.nb(sentences_mentioning_prior_victims ~ log1p(population) + after + death.day.num + after:death.day.num + I(death.day.num^2) + after:I(death.day.num^2) + (1|associated_name), 
#                  data=stories))


#summary(l1 <- lmer(wider.issue ~ gender + log.population + age + after + (1|associated_name), data=stories))
summary(l1 <- lmer(wider.issue ~ gender + age + log.population + after + (1|associated_name), data=stories))

summary(l1)
bindata = data.frame(after = c(FALSE, TRUE))#, story.day.num = c(0, michael.brown.day.num+14))
bindata$age <- median(stories$age)
bindata$log.population <- log1p(median(stories$population))
bindata$log.num.sentences = log1p(median(stories$num_sentences))

bindata$associated_name = sample(unique(subset(stories, gender="Male")$associated_name), 1)

bindata$gender = "Male"

fitted.prob.before <- 1/(1+exp(-1*(
                        summary(l1)$coefficients['(Intercept)',]['Estimate'] + 
                        summary(l1)$coefficients['genderMale',]['Estimate'] +
                        median(stories$age) * summary(l1)$coefficients['age',]['Estimate'] +
                        log1p(median(stories$population)) * summary(l1)$coefficients['log.population',]['Estimate']
#                        log1p(median(stories$num_sentences))* summary(l1)$coefficients['log.num.sentences',]['Estimate'] 
  )))


fitted.prob.after <- 1/(1+exp(-1*(
  summary(l1)$coefficients['(Intercept)',]['Estimate'] + 
    summary(l1)$coefficients['genderMale',]['Estimate'] +
    median(stories$age) * summary(l1)$coefficients['age',]['Estimate'] +
    log1p(median(stories$population)) * summary(l1)$coefficients['log.population',]['Estimate'] +
#    log1p(median(stories$num_sentences))* summary(l1)$coefficients['log.num.sentences',]['Estimate'] +
    summary(l1)$coefficients['afterTRUE',]['Estimate']
)))


summary(l2 <- lmer(wider.issue ~ gender + log.population + age + after + death.day.num + after:death.day.num + (1|associated_name), data=stories))


###############################
##### SHARING HYPOTHESIS ######
###############################
unique(stories$media_name)

summary(sh0 <- lmer(log1p(facebook_share_count) ~ 1 + (1|media_name) + facebook.delay.days, data=stories))
summary(sh1 <- lmer(log1p(facebook_share_count) ~ story.day.num + after + after:story.day.num + facebook.delay.days + log.population + age + gender + (1|media_name), data=stories))

s.sh1 <- summary(sh1)
sharedata <- data.frame(story.day.num = seq(min(stories$story.day.num), max(stories$story.day.num)))
sharedata$age <- median(stories$age)
sharedata$log.population <- log1p(median(stories$population))
sharedata$after <- sharedata$story.day.num > michael.brown.day.num
sharedata$facebook.delay.days <- mean(stories$facebook.delay.days)
sharedata$log.population <- log1p(median(stories$population))

# sharedata$dv <-  s.sh1$coefficients['(Intercept)',]['Estimate'] +
#   sharedata$story.day.num * s.sh1$coefficients['story.day.num',]['Estimate'] +
#   sharedata$age *  s.sh1$coefficients['age',]['Estimate'] +
#   sharedata$log.population *  s.sh1$coefficients['log.population',]['Estimate'] +
#   sharedata$facebook.delay.days *  s.sh1$coefficients['facebook.delay.days',]['Estimate'] +
#   sharedata$after *  s.sh1$coefficients['afterTRUE',]['Estimate'] +
#   sharedata$after * sharedata$story.day.num * s.sh1$coefficients['story.day.num:afterTRUE',]['Estimate']

#ggplot(stories, aes(story.day.num, facebook_share_count/facebook.delay.days, label=associated_name)) +
#  geom_jitter()
ggplot(stories, aes(story.day.num, facebook_comment_count, label=associated_name)) +
  geom_jitter()

ggplot(stories, aes(story.day.num, facebook_share_count, label=associated_name)) +
  geom_jitter()
