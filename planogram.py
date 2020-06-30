# %load planogram.py

# Function to convert shelf measurement to mm
def create_shelf_mm(fixture):
    fixture["shelf_width_mm"] = fixture["shelf_width_cm"]*10
    return fixture

# Function to arrange products according to profits per milimeter
def highest_profits_first(fixture, products):
    # Create mm shelf measurement
    create_shelf_mm(fixture) 
    
    # Sort Products by Profit_per_mm
    products["profit_per_mm"] = products["profit"]/products["product_width_mm"]
    products = products.sort_values("profit_per_mm", ascending=False)
    
    # Create new ideal_shelf column
    products["ideal_shelf"]= "None"
    
    # Set Total Profit at Zero
    total_profit = 0
    
    # Loop through all shelves
    for shelf_num in range(fixture.shape[0]):
        # Reset Master ideal shelf list
        ideal_shelf_list = []
        # Reset current shelf list
        items_on_shelf = []
        
        shelf_label = fixture["shelf_no"].iloc[shelf_num]
        space_left = fixture["shelf_width_mm"].iloc[shelf_num]
        
        # Loop through all products
        for product_num in range(products.shape[0]):
            current_shelf = products["ideal_shelf"].iloc[product_num]
            product_width = products["product_width_mm"].iloc[product_num]
            product_profit = products["profit"].iloc[product_num]
            product_id = products["product_id"].iloc[product_num]
            
            # If a product isn't shelved yet and can fit on a shelf
            if space_left >= product_width and current_shelf == "None":
                # Add product onto shelf and master list
                ideal_shelf_list.append(shelf_label)
                # Calculate amount of space left
                space_left -= product_width
                # Add product profit to total profit
                total_profit += product_profit
                # Append item onto a list
                items_on_shelf.append(product_id)
            else: 
                # If item doesn't fit, append its current status shelf onto master list
                ideal_shelf_list.append(current_shelf)
        # Update ideal_shelf column
        products["ideal_shelf"]=ideal_shelf_list
    
    return total_profit, products


# Final function to create a dataframe with most profitable placement of products
def planogram(fixture, products):
    """
    Arguments:
    - fixture :: DataFrame[["shelf_no", "shelf_width_cm"]]
    - products :: DataFrame[["product_id", "product_width_mm", "profit"]]

    Returns: DataFrame[["shelf_no", "product_id"]]
    """
    # Create a list of all possible permutations for index
    original_index = fixture.index.tolist()
    fixture_permutate = [list(x) for x in list(set(itertools.permutations(original_index)))]
    # Create empty list to nest profits and index
    profit_list = []
    #print (fixture_permutate)
    for index in fixture_permutate:
        profit = highest_profits_first(fixture.iloc[index], products)[0]
        df = highest_profits_first(fixture.iloc[index], products)[1]
        # Append a tuple of profit, index
        profit_list.append((profit, index, df))
    
    products = max(profit_list)[2]
    best_option_profit = max(profit_list)[0]
    max_possible_profit = products["profit"].sum()

    # Create a new column called "shelf_no"
    products["shelf_no"] = products["ideal_shelf"].copy()
    # Create a new df that does not half items not on shelves
    df = products[products["shelf_no"]!="None"][["shelf_no", "product_id"]]
    return df.sort_values("shelf_no")



if __name__ == "__main__":
    import numpy as np
    import pandas as pd
    import itertools

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--products",
        type=argparse.FileType(mode="r"),
        default="products.csv",
        help="products input file",
    )
    parser.add_argument(
        "--fixture",
        type=argparse.FileType(mode="r"),
        default="fixture.csv",
        help="fixture input file",
    )
    parser.add_argument(
        "--out", "-o", default="solution.csv", help="solution output file"
    )
    
    ### Dummy argument added here that allows function to run in Jupyter Notebooks
    ### Delete next three lines if this causes an error 
    parser.add_argument(
        '-f'
    )
    ###

    args = parser.parse_args()

    fixture = pd.read_csv(args.fixture)
    products = pd.read_csv(args.products)

    solution = planogram(fixture, products)

    solution.to_csv(args.out, index=False)

    print(
        "stats:",
        solution[["shelf_no", "product_id"]]
        .merge(fixture, on="shelf_no")
        .merge(products, on="product_id")
        .assign(n_products=1)
        .pivot_table(
            index=["shelf_no", "shelf_width_cm"],
            values=["n_products", "profit", "product_width_mm"],
            aggfunc=np.sum,
            margins=True,
        ),
        sep="\n",
    )

