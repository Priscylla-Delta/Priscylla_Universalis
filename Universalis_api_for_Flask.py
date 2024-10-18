from flask import request
import requests
import json

def main():

    # get all items ids sold on marketaboard
    marketable_Item_IDs = get_marketable_Item_IDs()
    # get all items ids and their corrosponding in game names
    ID_Mappings = get_Id_Mappings()

    # Create a dictionary of all marketable items and their corosponding in game names
    marketable_Item_Mapppings = get_marketable_Item_Mapppings(marketable_Item_IDs, ID_Mappings)

    validated_Input = get_validated_Input(marketable_Item_Mapppings)


    # Create a dictionary of all the listings for the given item and region
    listings = get_listings(validated_Input)

    # Use the listings and make a purchase order for the user
    purchase_Order = get_purchase_Order(listings, validated_Input)

    # Render the order in some Gui
    render_purchase_Order(purchase_Order, listings, validated_Input)

    return


def get_marketable_Item_IDs():

    # Get request for all items that can be sold on the mkb (Marketable items)
    marketable_Item_IDs = requests.get('https://universalis.app/api/v2/marketable', timeout=5)
    # Validate status code (200 = good)
    print("marketable_Item_IDs Status code: ",marketable_Item_IDs.status_code)
    # loads response into a list of all item id
    marketable_Item_IDs = json.loads(marketable_Item_IDs.text)
    
    # # debug structure of Item ids (Should be list)
    # print(marketable_Item_IDs)

    return marketable_Item_IDs


def get_Id_Mappings():

    # Get request for all item ids with their corosponding in game names
    ID_Mappings = requests.get('https://raw.githubusercontent.com/ffxiv-teamcraft/ffxiv-teamcraft/master/libs/data/src/lib/json/items.json', timeout=5)
    # Validate status code (200 = good)
    print("IDs_mapping Status code : ", ID_Mappings.status_code)
    # loades response into a dictionary of all item ids and their corosponding in game names
    ID_Mappings = ID_Mappings.json()    

    # # debug structure of Id mappings (Should be dictionary)
    # print(ID_Mappings)

    return ID_Mappings


def get_marketable_Item_Mapppings(marketable_Item_IDs, ID_Mappings):

    # intialized an empty dictionary 
    marketable_Item_Mapppings = {}
    # iterates through all item ids and adds them to the dictionary along with their english name
    for Item_ID in marketable_Item_IDs:
        marketable_Item_Mapppings[Item_ID] = ID_Mappings[str(Item_ID)]

    # # debug Structure of item mappings (Should be id : name)    
    # print(marketable_Item_Mapppings)
 
    return marketable_Item_Mapppings

def get_validated_Input(marketable_Item_Mapppings):
    
    item_Name = request.form.get("item_Name")
    
    # iterates through all available items, then iterates through all languages to compare with the given item name
    for item in marketable_Item_Mapppings:
        for language in marketable_Item_Mapppings[item]:
            if marketable_Item_Mapppings[item][language].lower() == item_Name.lower():
                # Fixes Capitalization errors
                item_Name = marketable_Item_Mapppings[item][language]
                # Obtains Item_ID
                item_id = str(item)

    region = request.form.get("region")
    quality = request.form.get("quality")
    quantity = int(request.form.get("quantity"))



    validated_Input = { "item_Name" : item_Name,
                        "item_ID" : item_id,
                        "region" : region,
                        "quality" : quality,
                        "quantity" : quantity }


    return validated_Input


def get_listings(validated_Input):

    # validated_Input = {"item_Name" : item_Name, "item_ID" : item_id, "region" : region, "quality" : quality, "quantity" : quantity}

    item_name = validated_Input["item_Name"]
    item_ID = validated_Input["item_ID"]
    region = validated_Input["region"]
    quality = validated_Input["quality"]

    print(f"Grabbing Listings for {quality} {item_name} ({item_ID}) in {region}")

    # Formatting Quality to True/False, as expected by the API
    if quality == "NQ":
        quality = False
    elif quality == "HQ":
        quality = True

    # Constructs a valid url with givin inputs
    market_Data_Url = f"https://universalis.app/api/v2/{region}/{item_ID}?entries=0&hq={quality}&statsWithin=0&fields=listings.pricePerUnit%2C+listings.worldName%2C+listings.quantity%2C+listings.total%2C+listings.listingID+%2C+listings.retainerName%2C+listings.hq%2C+listings.tax"

    # Get request for all the relevent market data for the given item and region (PricePerUnit, Quantity, WorldName, WorldID, ListingID, Total)
    market_Data = requests.get(market_Data_Url, timeout=5)
    # Validate status code (200 = good)
    print("market_Data Status code: ", market_Data.status_code)
    # loads response into a list of dictionaries for each listing and their fields
    listings = market_Data.json()['listings']
    
    # # debug Structure of listings (should be list of dictionaries with all their respective fields)
    # print(listings)
    

    # Make a dictionary of listings organized by their listingID
    # Initializes and empty Dictionary
    listing_IDs_Dict = {}

    # Iterates through each listing, intializing an empty dict with name equal to the listing ID
    for listing in listings:
        listing_IDs_Dict[listing['listingID']] = {}
        
        # Iterates through each field of the listing and copies them over to the new dictionary organized by id
        for field in listing:
            listing_IDs_Dict[listing['listingID']][field] = listing[field]
        
    # # Debugg for Validating Dictionary integrity         
    # print(listing_IDs_Dict)
    
    return listing_IDs_Dict


def get_purchase_Order(listings, validated_Input):
    
    quantity = validated_Input["quantity"]

    # Create a temporty listing to make edits for
    temp_listings = listings.copy()

    # Initialize a purchase order to store the list of listing Id's
    purchase_Order = []

    while quantity > 0:

        # If there are no listings left (ie all items are to be bought OR none are being sold)
        if len(temp_listings) == 0:
            return purchase_Order

        # Iterate through a copy of each listing's id and grab the quantity being sold
        for listing in list(temp_listings):
            listing_quantity = temp_listings[listing]['quantity']
            
            # If the listing quanitity is less or equal to the quantity being baught, subtract that amount
            # and add the listing id to the purchase order and remove the listingID from the listings Dict
            # such that the incrimentation backup doesnt reuse listings 
            if listing_quantity <= quantity:
                quantity = quantity - listing_quantity
                purchase_Order.append(listing)
                temp_listings.pop(listing)
                
                
            if quantity == 0:
                # If youve bought exactly enough, stop the loop
                # # Debugg for validating Purchase order structure, should be a list of Listing Ids
                # print(purchase_Order)
                return purchase_Order
            
        quantity += 1


def render_purchase_Order(purchase_Order, listings, validated_Input):

    item_name = validated_Input["item_Name"]
    item_ID = validated_Input["item_ID"]
    region = validated_Input["region"]
    quality = validated_Input["quality"]
    quantity = validated_Input["quantity"]

    total_Bought = 0
    total_Cost = 0
    total_item_Cost = 0
    total_Tax_Cost = 0
    average_Price_Per_Unit = 0.0
    price_Per_Units = []
    purchases = []

    for order in purchase_Order:
        listing = listings[order]

        # quality
        if listing["hq"] == True:
            quality = "HQ"
        else:
            quality = "NQ"

        # Increment Bought
        total_Bought += int(listing["quantity"])

        # Increment Unit cost
        item_Costs = int(listing["total"])
        total_item_Cost += item_Costs

        # Increment Tax cost
        tax_cost = int(listing["tax"])
        total_Tax_Cost += tax_cost
        
        # Increment Cost
        total_Cost += item_Costs + tax_cost

        # Append Price Per Units
        price_per_unit = float(listing["pricePerUnit"])
        price_Per_Units.append(price_per_unit)

        # Append individual purchases for dynamic rendering
        purchases.append({
            "quantity": listing["quantity"],
            "retainerName": listing["retainerName"],
            "worldName": listing["worldName"],
            "item_Costs": item_Costs,
            "price_per_unit": price_per_unit,
            "tax_cost": tax_cost,
            "total_Cost": total_Cost,
            "quality" : quality
        })

    # Compute Average
    average_Price_Per_Unit = round(sum(price_Per_Units) / len(price_Per_Units), ndigits=2)

    # Return the necessary data for dynamic rendering
    return {
        "item_Name": item_name,
        "item_ID" : item_ID,
        "region": region,
        "quality": quality,
        "quantity": quantity,
        "total_Bought": total_Bought,
        "total_Cost": total_Cost,
        "total_item_Cost": total_item_Cost,
        "total_Tax_Cost": total_Tax_Cost,
        "average_Price_Per_Unit": average_Price_Per_Unit,
        "purchases": purchases
    }


#main()