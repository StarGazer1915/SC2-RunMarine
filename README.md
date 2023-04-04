# SC2-RunMarine
Door: 
- Bram van Leusden (script-kidie)
- Justin Klein (StarGazer1915)
- Rutger Willard (unknownZandbak)
- Youssef Boulfiham (Youssef-Boulfiham)

## Inrichting omgeving
De simulatie vind plaats in het spel StarCraft II en wordt aangestuurd met behulp van een python API genaamd: `sc2`. We hebben voor deze API gekozen aangezien alle leden het beste met deze python variant overweg kunnen. Ook is veel documentatie en uitleg over de API beschikbaar via de link: https://pythonprogramming.net/commanding-army-starcraft-ii-ai-python-sc2-tutorial/. Hiernaast heeft starcraft 2 zijn eigen map builder en is/was het voor ons eenvoudig om meerdere omgevingen/situaties op te zetten voor onze simulaties. 

In de huidige simualtie probeert een agent (Marine) weg te rennen van een dodelijke vijand (Baneling). De tegenestander wordt aangestuurd door een computer en is hierdoor een onderdeel van de omgeving. De Agent heeft zijn eigen logica en waarneming van de omgeving waarmee hij een route probeert te vinden om te kunnen vluchten van de Baneling. Er zijn meerdere maps beschikbaar om deze functionaliteit in uit te testen. Wij hebben de functionaliteit van de Agent voornamelijk getest binnen de `marine_vs_baneling_advanced_NoOverlord` map.

## Architectuur, logica en onzekerheid
Als code architectuur is er uiteraard gekozen voor OOP, hiermee kunnen we het gedrag van één Agent makkelijk laten afwijken van een andere Agent zodat hopelijk in de toekomst meerdere inviduele agents de omgeving anders kunnen waarnemen (http://www2.econ.iastate.edu/tesfatsi/ABMAOPAMES.LT.pdf). Om eerst de interpretatie van de wereld goed te laten functioneren is er op dit moment één agent die probeert te vluchten. Het doel van onze agent is om te overleven. Deze agent beweegt door de omgeving heen (en staat stil wanneer er geen gevaar is) en geeft ieder coördinaat die hij ziet een score voor 'veiligheid'. Een coordinaat wordt als minder veilig beschouwt als deze zich in de buurt van muren bevindt en/of als de Agent ziet dat dit coördinaat in het zicht is van de tegenstander (de agent wilt namelijk uit het zicht blijven). Wanneer de Agent alle posities heeft beoordeeld kijkt hij eerst naar de hoogst scorende coördinaat. In het geval dat er meerdere coordinaten zijn met dezelfde score, dan pakt de agent het coördinaat welke het meest ver is van de Baneling. Wanneer de agent begint met vluchten heeft hij nog niet alle coordinaten verkend en weet de Agent dus niet waar wel en geen loopbaar terrein zich bevindt (onzekerheid). De agent aanschouwt alles wat nog niet verkend is als onloopbaar terein, hiermee voorkomt de agent dat hij naar een hoek loopt en zo kiest hij er juist voor om voorzichtig langzaam het onverkende gebied te verkennen. Het kan wel echter voorkomen dat hij het onbekende terrein zal moeten verkennen aangezien de Baneling hem aan het opjagen is.

## Gebruik
Om de simulatie te starten kunt u het `main.py` bestand uitvoeren. Let op dat u hiervoor wel een aantal libraries/packages, waaronder `sc2`, geïnstalleerd moet hebben. Zie hiervoor de imports van de `main.py`, `GameBot.py` en `MarineAgent.py` bestanden. Ook moet u uiteraard StarCraft II gedownload hebben op uw computer/machine om de omgevingen te kunnen laden.
