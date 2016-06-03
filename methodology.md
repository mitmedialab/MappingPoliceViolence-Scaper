Mapping Police Violence - Notes, Methodology, General Documentation
===================================================================

This work concerns a collaboration with BlackLivesMatter activist DeRay Mckesson seeking to evaluate if, and in what ways, mainstream press coverage of police killings has changed in the last few years. 

List of victims
---------------
There exist no 100% reliable lists of all victims of police violence, due to lack of transparency and poor documentation on the part of law enforcement agencies. This work relies on three databases which draw from news reporting, public record, and crowdsourced information in an attempt to comprehensively document victims of police violence. They are:
* [Mapping Police Violence](http://mappingpoliceviolence.org/) (MPV)
* [The Counted](http://www.theguardian.com/us-news/ng-interactive/2015/jun/01/the-counted-police-killings-us-database), by the Guardian
* [Police Shootings](https://www.washingtonpost.com/graphics/national/police-shootings/), by the Washington Post

Analysis of police violence in 2014 relies solely on the list of [unarmed black victims](http://mappingpoliceviolence.org/unarmed2014/) provided by MPV. Analysis of police violence in 2015 relies on a combined list from all three sources.

Measurement of media coverage
-----------------------------
We initially avoid examining type or tone, and examine only quantity of media coverage about each victim. For each victim, we retrieve from MediaCloud:
* links to all US mainstream news stories in the timeframe (d-5, d+14), where d is the date of the incident--that is, stories in a timeframe from five days before to two weeks after.
* total number of news stories written about the victim in the specified timeframe
* total number of news stories written in total in the specified timeframe

This timeframe is chosen because anecdotally, news coverage of an event often ends after two or three days, and very rarely persists after two weeks. The two-week window should therefore provide a reasonable snapshot of primary coverage while excluding post-hoc secondary coverage, which might for instance be more concerned with follow-up events, investigations, trials, or activism around the victim's death. We also include the five days prior to capture coverage of the events leading up to the victim's death (for instance, if a victim was arrested and injured and then died in custody a few days later).

### Ambiguities and disputed data

#### Definition of "unarmed"
MPV codes victims as "unarmed" based on guidelines published [here](http://mappingpoliceviolence.org/aboutthedata/); most notably, they classify victims "holding a toy weapon" as unarmed. This is a discrepancy from both the Guardian and WaPo; the Guardian distinguishes between codings of "unarmed" and "non-lethal firearm", while WaPo distinguishes between "unarmed" and "toy weapon". The decision of whether victims holding toy weapons should be classified as "armed" or "unarmed" is both unobvious and political. Our list includes all black victims coded by our sources as "unarmed", "uncertain/disputed", and "toy weapon/non-lethal firearm", and we include the original coding in our spreadsheet.

#### Date of incident
MPV lists the date as "date of injury resulting in death" while WaPo and the Guardian only say they list the "date." This results in some discrepancies in the date of the "event." For one-day discrepancies, we use the earlier date. Freddie Gray and Natasha McKenna have larger discrepancies due to the particular circumstances of their deaths:
* Gray fell into a coma during his arrest on 4/12, and died a week later on 4/19
* McKenna had a heart attack after being tasered on 2/3, and was removed from life support on 2/8.
For Gray and McKenna, we use the dates of their deaths to timeframe the queries.

### Query adjustments
Specifying a MediaCloud query that retrieves all the reportage of a victim while excluding irrelevant stories is often more complicated than simply querying the victim's name; for instance, many victims share names with prominent public figures (like Jerry Brown, who shares a name with the California governor) or have names that are otherwise common (like Robert Baltimore). Each query was manually entered on [Dashboard](https://dashboard.mediameter.org/), and the sentences sampled in the "Mentions: Sentences Matching" box were manually checked to ensure that all the stories found are relevant. If a victim has multiple names, name variants, or name misspellings (for instance, "Asshams Manley" and "Asshams Pharoah Manley"), the query was adjusted to `name1 OR name2 OR name3 OR ...`. If irrelevant stories were found, the query was adjusted to exclude irrelevant stories; for instance, `Jerry Brown` was adjusted to `"Jerry Dwight Brown" OR ("jerry brown" AND (pasco OR zephyrhills OR fl OR florida))) AND -(gov* or CA or california or sacramento or democrat*)` to exclude references to the California governor.