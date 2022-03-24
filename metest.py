import csv
from operator import add, itemgetter
from os import getenv
from turtle import title
from webbrowser import get
import discord
from discord.ext import commands
from googletrans import Translator
import requests
import json
import math
import config

token = config.token
key = config.key

bot = commands.Bot(command_prefix="!")

def convert_to_sol (num):
    return num/1000000000

def get_floor_price(collection):
    url = "http://api-mainnet.magiceden.dev/v2/collections/"+ collection + "/stats"
    payload={}
    headers = {
        "Key": key
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)

    return convert_to_sol(data["floorPrice"])

def add_floor_prices(floor_price_dict):
    return math.fsum(floor_price_dict.values())

def translate(msg, lang):
    translator = Translator()
    translation = translator.translate(msg, dest=lang)
    
    return translation.text

def get_ME(url):
    payload={}
    headers = {
        "Key": key
    }
    req = requests.request("GET", url, headers=headers, data=payload)
    ME_info = json.loads(req.text)

    return ME_info

def get_Name(collectionName):
    url = "http://api-mainnet.magiceden.dev/v2/collections/{}".format(collectionName)
    payload={}
    headers = {
        "Key": key
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)

    return data['name']

def construct_embed(place, name, collection_url, image_url):
    embed = discord.Embed ( 
        title = place + " " + name + " " + "- Magic Eden Link",
        url = collection_url
    )
    embed.set_image(url = image_url)
    return embed


@bot.command()
async def portfolio(ctx, wallet_address):
    wallet = wallet_address
    nfts_owned = []
    min_portfolio_value = 0
    # Get 500 NFT Tokens owned by wallet into a json
    url = "http://api-mainnet.magiceden.dev/v2/wallets/" + str(wallet) + "/tokens?offset=0&limit=500"
    payload={}
    headers = {
        "Key": key
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    # Dump HTTP response into a json object
    data = json.loads(response.text)

    floor_prices = {}
    real_names = {}
    collection_urls = {}
    unique_collections = set()
    for entry in data:

        # If the collection is not on ME
        if "collection" not in entry:
            continue

        nft = {}

        nft["image_url"] = entry["image"]
        nft["collection_name"] = entry["collection"]
        collection_name = entry["collection"]

        if collection_name not in unique_collections:
            unique_collections.add(collection_name)
            nft["floor_price"] = get_floor_price(entry["collection"])
            floor_prices[collection_name] = nft["floor_price"]

            nft["real_name"] = get_Name(entry["collection"])
            real_names[collection_name] = nft["real_name"]

            collection_info = get_ME("http://api-mainnet.magiceden.dev/v2/collections/{}".format(entry["collection"]))
            collection_url = "http://magiceden.io/marketplace/{}".format(collection_info["symbol"])
            nft["collection_url"] = collection_url
            collection_urls[collection_name] = nft["collection_url"]
        elif collection_name in unique_collections:
            nft["floor_price"] = floor_prices[collection_name]
            nft["real_name"] = real_names[collection_name]
            nft["collection_url"] = collection_urls[collection_name]

        nfts_owned.append(nft)
        min_portfolio_value += nft["floor_price"]
    top3 = sorted(nfts_owned, key=itemgetter("floor_price"), reverse=True)[:3]
    counter = 1
    
    await ctx.channel.send ("**Minimum Portfolio Value: **" + str(round(min_portfolio_value, 3)) + " SOL\n" + 
    "**The top 3 NFTs for wallet " + str(wallet) + " are: **\n" + "\n" )
    for nft in top3:
        await ctx.channel.send(embed = construct_embed(":first_place:", nft["real_name"], nft["collection_url"], nft["image_url"]))
        counter += 1
    print(top3)

@bot.command()
async def collection(ctx, req, lang = ''):
    collection_info = get_ME("http://api-mainnet.magiceden.dev/v2/collections/{}".format(req))
    collection_stats = get_ME("http://api-mainnet.magiceden.dev/v2/collections/{}/stats".format(req))

    collection_name = collection_info['name']
    collection_description = collection_info['description']
    collection_image = collection_info['image']

    collection_fp = convert_to_sol(collection_stats['floorPrice'])
    active_listing = collection_stats['listedCount']

    if lang == '': 
        lang = 'en'

    response = "**{}**\n".format(collection_name) + translate("{}\n**Floor price:** {}\n**Active listings:** {}\n{}\n".format(
        collection_description,collection_fp,active_listing,collection_image), lang)
    
    await ctx.channel.send(response)

bot.run(token)