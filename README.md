A little suite of scripts used for finding out handy things about London. And parking.

### Getting postcodes of interest
Specify a radius (r) and an initial postcode and the script will head off and grab all of the postcodes in an r km radius of the postcode you've specified. This is all written to a file called `postcodes_of_interest.csv`. 

### Getting valuation data from postcodes
Given the file `postcodes_of_interest.csv` this script will go to the Government valuations website and run searches against each of the 'areas' (postcode minus the last number and letter). This currently only looks at categories 'CP' and 'CP1' i.e. car parking. This information is all downloaded, formatted and put into `valuationData.csv`.

### Getting planning applications data from postcodes
The script `get_planning_data.py` can be used with a list of postcodes to automatically grab all the planning application data (from Islington council website) from those postcodes. However, it's pretty slow and generates quite a few requests (>2000) so I think you're best using...

### Getting planning applications from ward name
The script `get_all_planning_data.py` gets all of the planning application information held on the Islington council website. Rather than going through postcode by postcode it selects each ward in turn and then iterates over all of the pages returned for a more expensive initial query but many fewer queries. Seems to be much quicker and is less likely to take the council website down.

### Plotting some of the data
The script `my_plotter.py` basically shows how complicated it is to produce a reasonable(ish) postcode graph in Python. Honestly, it's a nightmare. But any way, I've not included all of the data required to be able to do the plotting but here's how to get it:
1. Clone this repo
2. Run this command: `wget http://www.opendoorlogistics.com/wp-content/uploads/Data/UK-postcode-boundaries-Jan-2015.zip`
3. Run this command: `unzip UK-postcode-boundaries-Jan-2015.zip -d uk_postcodes`
4. Run this command: `wget http://sensitivecities.com/extra/london.zip`
5. Run this command: `unzip london.zip -d data`

Then you're going to have to install all the dependencies. No telling how hard that's going to be. But then you can run the script and get something like this:

![Parking Density](london_parking.png)

So that's just something simple - namely, the parking area density per postcode area, within N kilometers of Angel station.

### Examining planning applications data
The script `parse_planning_data.py` is probably the simplest of the bunch. It goes through the planning data, gets rid of any tricky rows and then looks at which 'change of use' planning applications have recently been refused. 

### Further steps
Were I to try to use these two datasets (valuations and planning applications) I'd remove the filter on parking spaces on the valuations script. This would give me all the business rates (that weren't parking) in our target area. I'd have to do fuzzy matching to find out how many of those premises recently had failed change of use planning applications (probably wouldn't be loads). At that point you've got the location and area of land that has likely recently taken a dive in price. 

If you're feeling jazzy you can combine that info with the parking space density of an area to order sites in importance.

As a bonus, a commercial developer could almost certainly use this information (but it'd be tricky). Look at all the times planning applications have been rejected in the past and then investigate the change in value of house/commercial prices in the local area (likely to be a small, but non-negligble effect). Get the planning application data as soon as possible (immediately) and you've got an edge. You could also use the information when thinking about purchasing similar properties.
