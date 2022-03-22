import csv
from operator import add
#from dotenv import load_dotenv
from os import getenv
from discord.ext import commands
import requests
import json
import math
import config

#load_dotenv()
token = config.token

bot = commands.Bot(command_prefix="!")

@bot.command()
async def llama(ctx, llama_number):
    with open('Llama_master.csv', 'r') as llamaFile:
        reader = csv.reader(llamaFile)

        for row in reader:
            if row[0] == llama_number:
                image = row[2]
                rarity = row[3]

    response = ' Llama #{} is {}! \n'.format(llama_number, rarity)
    await ctx.channel.send(response)
    await ctx.channel.send(image)

def convert_to_sol (num):
    return num/1000000000

def get_floor_price(collection):
    url = "http://api-mainnet.magiceden.dev/v2/collections/"+ collection + "/stats"
    payload={}
    headers = {
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)

    return convert_to_sol(data["floorPrice"])

def add_floor_prices(floor_price_dict):
    return math.fsum(floor_price_dict.values())

@bot.command()
async def portfolio(ctx, wallet_address):
    wallet = wallet_address

    # Get 500 NFT Tokens owned by wallet into a json
    url = "http://api-mainnet.magiceden.dev/v2/wallets/" + str(wallet) + "/tokens?offset=0&limit=500"
    payload={}
    headers = {
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    # Dump HTTP response into a json object
    data = json.loads(response.text)

    # Initialize empty array and dictionaries we will use later
    nfts_owned = []
    images = {}
    floor_prices = {}
    min_portfolio_value = 0

    # Gather floor price for all nfts owned by wallet
    for nft in data:
        # NFTs that are not on Magic Eden are missing the collection field
        # If the nft does not have a collection attribute it is not on ME so we skip
        if not nft["collection"]:
            continue

        nft_name = nft["name"]
        collection_name = nft["collection"]

        # Grab image link and add it to images dict
        image_link = nft["image"]
        images[collection_name] = image_link

        # Only add collection to floor_prices dictionary if it hasnt been added before
        if collection_name not in floor_prices:
            floor_prices[collection_name] = None
        
        # Get floor price for collections only if it has not been added before
        if not floor_prices[collection_name]:
            floor_prices[collection_name] = get_floor_price(collection_name)
        
        # Take care of duplicate NFT's from same collection
        min_portfolio_value += floor_prices[collection_name]
        # Add the specific nft into the nfts_owned array
        nfts_owned.append(nft_name)

    print(floor_prices)

    top3 = sorted(floor_prices, key=floor_prices.get, reverse=True)[:3]

    image_links = []
    for item in top3:
        image_links.append(images[item])

    # images[top3[collection_name]]

    # Add up all floor prices
    # min_portfolio_value = add_floor_prices(floor_prices)

    await ctx.channel.send ("**Minimum Portfolio Value: **" + str(round(min_portfolio_value, 3)) + " SOL\n" +
    "The top 3 Nfts are " +
    image_links[0] + "\n" +
    image_links[1] + "\n" +
    image_links[2] 
    )
    # Call token mint for each token
    # Gather Floor price for each collection
    await ctx.channel.send(nfts_owned)


bot.run(token)