library(ggplot2)
library(lubridate)
library(stargazer)
library(texreg)
library(gmodels) # Contains CrossTable
require(MASS) # Contains glm.nb


rm(list=ls())

people <- read.csv("data/people-dataset.csv")


################################
### MODEL IDEAS AND GOALS
################################

### HYPOTHESIS 1: On average in the population of black people 
### killed by the police in the US between 2013 and 2016, there was a greater
### incidence rate of articles about that person's death in the following two weeks
### after the death of Michael Brown, holding all else constant

#### BASIC MODELS
### num_articles ~ age + gender + log1p(population) + weekend + day.num + after.brown + day.num:after.brown

### num_publishers (as a backup confirmatory hypothesis)

### total_facebook_shares ~ age + gender + log1p(population) + weekend + day.num + after.brown + day.num:after.brown

####### POTENTIAL FURTHER COVARIATES
#### CHARACTERISTICS OF THE PERSON OR INCIDENT
### mentall_illness
### armed
### cause of death?
#### CHARACTERISTICS OF CONTEXT
### state (unsure if we want to control for this)
#### CHARACTERISTICS OF TIME
### last_8_weeks_in_same_city (or other factors) <- let's look at one of these
### last_8_weeks (or other factors) <- let's look at one of these

################################
### SUMMARY STATISTICS AND
### EXPLORATORY DATA ANALYSIS
################################

## NUMBER OF DAYS SINCE FIRST OBSERVATION
people$ctdate = as.POSIXct(people$date)
people$day.num <- as.integer(difftime(people$ctdate, min(people$ctdate), unit="days"))

## GET THE DAY NUMBER FOR MICHAEL BROWN'S DEATH
brown.day.num <- subset(people, name=="Michael Brown")$day.num[[c(1)]]

## STEP ONE: REMOVE MICHAEL BROWN AND ANYONE WHO DIED IN THE TWO WEEK PERIOD BEFORE HIS DEATH
omitted <- subset(people, (day.num <= brown.day.num) & (day.num > brown.day.num - 14))
people <- subset(people, (day.num > brown.day.num) | (day.num < brown.day.num - 14))

################################
### UNIVARIATE ANALYSIS

## AGE
summary(people$age)
hist(people$age)

## GENDER
summary(people$gender)
people$gender.male <- people$gender == "Male"
summary(people$gender.male)

## DATES
people$weekday.name = wday(people$ctdate, label = TRUE)
people$weekday.number = wday(people$ctdate)
people$weekend = ifelse((people$weekday.number==7 | people$weekday.number==0), 1, 0)

min(people$ctdate)
max(people$ctdate)

summary(people$weekday.name)
hist(people$weekday.number)

summary(factor(people$weekend))

people$month <- month(people$ctdate)
summary(factor(people$month))
hist(people$month, breaks=12)

## BINARY: BEFORE OR AFTER MICHAEL BROWN'S DEATH
# AUGUST 9, 2014
people$after.brown <- people$ctdate > as.POSIXct("2014-08-09")
summary(people$after.brown)

## STATE
summary(people$state)

## CITY & CITY POPULATION
summary(people$city)

summary(people$population)
hist(log1p(people$population))

## ARMED 
## FOR NOW WE OMIT, BECAUSE IT'S NOT CLEAR
## TODO: DETERMINE MORE CLEARLY
summary(people$armed.)

## CAUSE OF DEATH
summary(people$cause_of_death)

## MENTAL ILLNESS
summary(people$mental_illness.)

## NUMBER OF ARTICLES IN TWO WEEKS
summary(people$num_articles)
hist(log1p(people$num_articles), breaks=20)

## NUMBER OF PUBLISHERS IN TWO WEEKS
summary(people$num_publishers)
hist(log1p(people$num_publishers), breaks=20)

## TOTAL BITLY CLICKS
summary(people$total_bitly_clicks)
hist(log1p(people$total_bitly_clicks), breaks=20)

## TOTAL FACEBOOK SHARES
summary(people$total_facebook_shares)
hist(log1p(people$total_facebook_shares), breaks=20)

## CUMULATIVE BITLY + FACEBOOK
people$total_social_media <- people$total_bitly_clicks + people$total_facebook_shares
hist(log1p(people$total_social_media))

################################
### BIVARIATE ANALYSIS
#
# - pre/post michael brown
# - outcome: number of articles
# - outcome: number of media outlets
# - outcome: number of social media shares


## PRE / POST MICHAEL BROWN AND ARTICLE COUNT
ggplot(people, aes(factor(after.brown), log1p(num_articles), label = name)) + 
  geom_violin() +
  geom_jitter() +
  geom_text()

## PRE / POST MICHAEL BROWN AND NUM PUBLISHERS
ggplot(people, aes(factor(after.brown), log1p(num_publishers), label = name)) + 
  geom_violin() +
  geom_jitter() +
  geom_text()

## PRE / POST MICHAEL BROWN AND FACEBOOK SHARES
ggplot(people, aes(factor(after.brown), log1p(total_facebook_shares), label = name)) + 
  geom_violin() +
  geom_jitter() +
  geom_text()

## PRE / POST MICHAEL BROWN AND BITLY CLICKS
ggplot(people, aes(factor(after.brown), log1p(total_bitly_clicks), label = name)) + 
  geom_violin() +
  geom_jitter() +
  geom_text()

missing_bitly <- subset(people, is.na(total_bitly_clicks)==TRUE)

## NUM ARTICLES AND CITY POPULATION
ggplot(people, aes(log1p(population), log1p(num_articles), label = name, colour = after.brown)) + 
  geom_point()# +
#  geom_text()

## FACEBOOK SHARES AND CITY POPULATION
ggplot(people, aes(log1p(population), log1p(total_facebook_shares), label = name, colour = after.brown)) + 
  geom_point()# +
#  geom_text()

## NUM ARTICLES AND WEEKEND
ggplot(people, aes(factor(weekend), log1p(num_articles), label = name)) + 
  geom_violin() +
  geom_jitter()

## SOCIAL MEDIA AND WEEKEND
ggplot(people, aes(factor(weekend), log1p(total_facebook_shares), label = name)) + 
  geom_violin() +
  geom_jitter()

## NUM ARTICLES AND MONTH NUM
ggplot(people, aes(month, log1p(num_articles), label = name, colour = after.brown)) + 
  geom_point()

## SOCIAL MEDIA AND MONTH NUM
ggplot(people, aes(month, log1p(total_facebook_shares), label = name, colour = after.brown)) + 
  geom_point()

################################
### TRIVARIATE ANALYSIS

## CHECK OVERLAP ACROSS THE THREE DATA SOURCES

## this fields notes: were they noticed by a source
## and also labeled as unarmed
CrossTable(people$in_mpv,people$in_guardian,
           expected=FALSE, prop.r=FALSE, prop.c=FALSE,
           prop.t=FALSE, prop.chisq=FALSE )

CrossTable(people$in_mpv,people$in_wapo,
           expected=FALSE, prop.r=FALSE, prop.c=FALSE,
           prop.t=FALSE, prop.chisq=FALSE )

CrossTable(people$in_guardian,people$in_wapo,
           expected=FALSE, prop.r=FALSE, prop.c=FALSE,
           prop.t=FALSE, prop.chisq=FALSE )

################################
### MODELING HYPOTHESES
################################
people$population.ln = log1p(people$population)

#num_articles ~ age + gender + log1p(population) + weekend + day.num + after.brown + day.num:after.brown

################################
### EXPLORE ZERO INFLATION

people$zero.num.articles <- people$num_articles == 0
people$zero.total.facebook.shares <- people$total_facebook_shares == 0

## We can't predict zeroes in the number articles very well (omit)
hist(log1p(people$num_articles), breaks=20)
bzna1 <- glm(zero.num.articles ~ 1, family = binomial,data=people)
bzna2 <- glm(zero.num.articles ~ population.ln + age + gender.male, family = binomial, data=people)
stargazer(bzna1, bzna2, type="text", star.cutoffs = c(0.05, 0.01, 0.001))


### MIGHT WANT A ZERO-INFLATED MODEL FOR SHARES
### BUT ONLY IF WE WANT TO INCLUDE PUBLICATION INFORMATION 
### AS COVARIATES IN THE MODEL OF SOCIAL MEDIA ACTIVITY
hist(log1p(people$total_facebook_shares), breaks=20)
bznf1 <- glm(zero.total.facebook.shares ~ 1, family = binomial,data=people)
bznf2 <- glm(zero.total.facebook.shares ~ population.ln + age + gender.male, family = binomial, data=people)
bznf3 <- glm(zero.total.facebook.shares ~ population.ln + age + gender.male + num_publishers, family = binomial, data=people)
bznf4 <- glm(zero.total.facebook.shares ~ population.ln + age + gender.male + num_articles, family = binomial, data=people)
bznf5 <- glm(zero.total.facebook.shares ~ population.ln + age + gender.male + num_publishers + num_articles, family = binomial, data=people)
stargazer(bznf1, bznf2, bznf3, bznf4, bznf5, type="text", star.cutoffs = c(0.05, 0.01, 0.001))


################################
### TEST HYPOTHESIS OF A DIFFERENCE IN NUMBER OF ARTICLES
### AFTER THE DEATH OF MICHAEL BROWN (see above for full statement)

summary(pna1 <- glm(num_articles ~ age + gender.male + population.ln + 
                    weekend + day.num + after.brown + day.num:after.brown, 
                  family="poisson", data=people))

summary(nbna1 <- glm.nb(num_articles ~ age + gender.male + population.ln + 
                      weekend + day.num + after.brown + day.num:after.brown, data=people))


#### REJECT THE POISSON MODEL
#### TODO: COME BACK AND DO THE MATH RIGHT
#X2 <- 2 * (logLik(nbna1) - logLik(pna1))
#pchisq(X2, df = 1, lower.tail=FALSE)
stargazer(pna1, nbna1, type="text")

summary(nbna2 <- glm.nb(num_articles ~ age + gender.male + population.ln + 
                          weekend + day.num, data=people))
summary(nbna3 <- glm.nb(num_articles ~ age + gender.male + population.ln, data=people))
summary(nbna4 <- glm.nb(num_articles ~ age + gender.male, data=people))
summary(nbna5 <- glm.nb(num_articles ~ 1, data=people))

### CREATE A QUADRATIC NB Model
summary(nbna6 <- glm.nb(num_articles ~ age + gender.male + population.ln + 
                          weekend + day.num + I(day.num^2) + after.brown + day.num:after.brown, data=people))


stargazer(nbna1,nbna2,nbna3,nbna4,nbna5, type="text")

#############################
#### TEST HYPOTHESIS OF A DIFFERENCE IN SOCIAL MEDIA SHARES

summary(psm1.total <- glm(total_facebook_shares ~ age + gender.male + population.ln + 
                      weekend + day.num + after.brown + day.num:after.brown, 
                    family="poisson", data=people))

summary(psm1.relative <- glm(total_facebook_shares ~ age + gender.male + population.ln + 
                            weekend + day.num + num_articles + after.brown + day.num:after.brown, 
                          family="poisson", data=people))

summary(nbsm1.total <- glm.nb(total_facebook_shares ~ age + gender.male + population.ln + 
                          weekend + day.num + after.brown + day.num:after.brown, data=people))

summary(nbsm1.relative <- glm.nb(total_facebook_shares ~ age + gender.male + population.ln + 
                          weekend + day.num + num_articles + after.brown + day.num:after.brown, data=people))

stargazer(psm1.total,nbsm1.total,psm1.relative,nbsm1.relative, type="text")


################################
### PLOTTING MODEL RESULTS
################################

################################
### PLOT THE MODEL FOR THE NUMBER OF ARTICLES
summary(nbna1)
# age
# gender
# log1p(population)
# weekend
# day.num
# after.brown <-- MAIN HYPOTHESIS PREDICTOR
# day.num:after.brown <-- MAIN HYPOTHESIS INTERACTION

#m=nbna1
m=nbna6
cat1 <-NULL
pf <-NULL
p<-NULL
p = data.frame(day.num = seq(min(people$day.num), max(people$day.num), 1))

p$age = mean(people$age)
p$gender.male = TRUE
p$population.ln = mean(log1p(people$population))
p$after.brown = ifelse(p$day.num>brown.day.num , TRUE,FALSE)
p$weekend = 0

cat1 <-predict(m, newdata=p, type="link",conf.int=TRUE, se.fit=TRUE)

critval <- 1.96

pf <- p
pf$log_upr <- cat1$fit + (critval * cat1$se.fit)
pf$log_lwr <- cat1$fit - (critval * cat1$se.fit)
pf$log_num_articles <- cat1$fit

pf$num_articles <- m$family$linkinv(pf$log_num_articles)
pf$upr2 <- m$family$linkinv(pf$log_upr)
pf$lwr2 <- m$family$linkinv(pf$log_upr)



### PLOT FULL VERSION
ggplot(pf, aes(x = day.num, y=num_articles)) +
  geom_vline(xintercept=c(brown.day.num), linetype="dashed", size=1, color="gray") +
  geom_line(data=pf,size = 1) +
  geom_ribbon(aes(ymin=pf$lwr2, ymax=pf$upr2), alpha=0.1) +
#  geom_point(data=people,aes(x=people$day.num, y=people$num_articles), alpha=.9, position=position_jitter(h=.2), color="red") +
#  geom_text(data=people,aes(label=name), size=3, alpha=0.8) + 
  #  geom_vline(xintercept=c(221,235), linetype="dotted") +
  ggtitle("Predicted Articles Per Black Person Killed By The Police or who Died in Police Custody, by Death Date")


### PLOT LOGGED VERSION
ggplot(pf, aes(x = day.num, y=log_num_articles)) +
  geom_vline(xintercept=c(brown.day.num), linetype="dashed", size=1, color="gray") +
  geom_line(data=pf,size = 1) +
  ylim(-3,10) +
  geom_ribbon(aes(ymin=pf$log_lwr, ymax=pf$log_upr), alpha=0.2, fill="red") +
  geom_jitter(data=people,aes(x=people$day.num, y=log1p(people$num_articles)), alpha=.9, color="red") +
#  geom_text(data=people,aes(label=name), size=3, alpha=0.8) + 
  ggtitle("Predicted Articles Per Black Person Killed By The Police or who Died in Police Custody, by Death Date")
