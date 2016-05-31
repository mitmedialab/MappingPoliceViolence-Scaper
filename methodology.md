Mapping Police Violence - Notes, Methodology, General Documentation
===================================================================

This work concerns a collaboration with BlackLivesMatter activist DeRay Mckesson seeking to evaluate if, and in what ways, mainstream press coverage of police killings has changed in the last few years. 

List of victims
---------------
There exist no 100% reliable lists of all victims of police violence, due to lack of transparency and poor documentation on the part of law enforcement agencies. This work relies on three databases which draw from news reporting, public record, and crowdsourced information in an attempt to comprehensively document victims of police violence. They are:
* [Mapping Police Violence](http://mappingpoliceviolence.org/) (MPV)
* [The Counted](http://www.theguardian.com/us-news/ng-interactive/2015/jun/01/the-counted-police-killings-us-database), by the Guardian
* [Police Shootings](https://www.washingtonpost.com/graphics/national/police-shootings/), by the Washington Post

Analysis of police violence in 2014 relies solely on the list of [unarmed black victims](http://mappingpoliceviolence.org/unarmed2014/) provided by MPV. Analysis of police violence in 2015 relies on lists from the Guardian and WaPo.

### Definition of "unarmed"
MPV codes victims as "unarmed" based on guidelines published [here](http://mappingpoliceviolence.org/aboutthedata/); most notably, they classify victims "holding a toy weapon" as unarmed. This is a discrepancy from both the Guardian and WaPo; the Guardian distinguishes between codings of "unarmed" and "non-lethal firearm", while WaPo distinguishes between "unarmed" and "toy weapon". The decision of whether victims holding toy weapons should be classified as "armed" or "unarmed" is both unobvious and political.

Measurement of media coverage
-----------------------------
We initially avoid examining type or tone, and examine only quantity of media coverage about each victim. For each victim, we retrieve from MediaCloud:
* links to all news stories in the timeframe (d-5, d+14), where d is the date of the killing--that is, the number of stories in a timeframe from five days before death to two weeks after death.
* total number of news stories written about the victim in the specified timeframe
* total number of news stories written in total in the specified timeframe

This timeframe is chosen because anecdotally, news coverage of an event often ends after two or three days, and very rarely persists after two weeks. The two-week window should therefore provide a reasonable snapshot of primary coverage while excluding post-hoc secondary coverage, which might for instance be more concerned with follow-up events, investigations, trials, or activism around the victim's death.

Specifying a MediaCloud query that retrieves all the reportage of a victim while excluding irrelevant stories is often more complicated than simply querying the victim's name; for instance, many victims share names with prominent public figures (like Jerry Brown, who shares a name with the California governor) or have names that are otherwise common words (like Robert Baltimore). As such, the results of each query were manually checked, and the query was modified as necessary until no irrelevant stories were included.

(more details on query adjustments go here)

