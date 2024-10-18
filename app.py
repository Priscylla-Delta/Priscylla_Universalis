from flask import Flask, render_template
import Universalis_api_for_Flask as api


app = Flask(__name__)
#UWU

@app.route('/')
def get_request():

    valid_names = []

    # get all items ids sold on marketaboard
    marketable_Item_IDs = api.get_marketable_Item_IDs()

    # get all items ids and their corrosponding in game names
    ID_Mappings = api.get_Id_Mappings()

    # Create a dictionary of all marketable items and their corosponding in game names
    marketable_Item_Mapppings = api.get_marketable_Item_Mapppings(marketable_Item_IDs, ID_Mappings)

    # print(marketable_Item_Mapppings)

    for item in marketable_Item_Mapppings:
        for language in marketable_Item_Mapppings[item]:
            valid_names.append(marketable_Item_Mapppings[item][language])
            # print(marketable_Item_Mapppings[item][language])

    # print(valid_names)

    valid_Regions = ['Japan', 'Europe', 'North-America', 'Oceania', 'China']
    valid_Qualities = ['HQ', 'NQ', 'Either']

    # Renders Search Page
    return render_template("search.html", valid_names = valid_names, valid_Regions = valid_Regions, valid_Qualities = valid_Qualities)

@app.route('/search', methods=["POST"])
def Search():

    # get all items ids sold on marketaboard
    marketable_Item_IDs = api.get_marketable_Item_IDs()

    # get all items ids and their corrosponding in game names
    ID_Mappings = api.get_Id_Mappings()

    # Create a dictionary of all marketable items and their corosponding in game names
    marketable_Item_Mapppings = api.get_marketable_Item_Mapppings(marketable_Item_IDs, ID_Mappings)


    validated_Input = api.get_validated_Input(marketable_Item_Mapppings)

    # Create a dictionary of all the listings for the given item and region
    listings = api.get_listings(validated_Input)

    # Use the listings and make a purchase order for the user
    purchase_Order = api.get_purchase_Order(listings, validated_Input)

    # rewritten function that compiles all the purchase order data into a json that can be rendered with a flask template
    result_data = api.render_purchase_Order(purchase_Order, listings, validated_Input)


    return render_template('search_results.html', result=result_data)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000,
            use_reloader=True, threaded=True)


