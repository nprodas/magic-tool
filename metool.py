from os import getenv
from discord.ext import commands
from discord import Embed
from googletrans import Translator
from languages import supported_LANGUAGES
from sql import create_connection
from sql import execute_read_query
from sql import execute_query
import requests
import json
import math
from dotenv import load_dotenv

load_dotenv()

token = getenv("token")
key = getenv("key")
password = getenv("password")

languages = supported_LANGUAGES

conn = create_connection(
    'magic-tool-db.csv4tgeuvsjv.us-east-1.rds.amazonaws.com', 
    'magic_admin', 
    password, 
    'magic_tool_db')

bot = commands.Bot(command_prefix="!")

def add_floor_prices(fp_list):
    return math.fsum(fp_list)

def convert_to_sol (num):
    return num/1000000000

def translate(msg, channel_ID):
    channels = execute_read_query(conn, "SELECT * FROM discord_channels")

    for channel in channels:
        if channel_ID == channel['ch_ID']:
            lang = channel['ch_Language'] 
    
    translator = Translator()
    translation = translator.translate(msg, dest= lang)
    
    return translation.text

def get_ME(url):
    payload={}
    headers = {"Key": key}
    req = requests.request("GET", url, headers=headers, data=payload)
    ME_info = json.loads(req.text)

    return ME_info

@bot.command()
async def portfolio(ctx, wallet):

    data = get_ME("http://api-mainnet.magiceden.dev/v2/wallets/{}/tokens?offset=0&limit=500".format(wallet))   

    unique_collections = list({entry['collection']:entry for entry in data if entry.__contains__('collection')}.values())
    unique_collections = [value['collection'] for value in unique_collections]
    unique_collections_info = []

    for collection in unique_collections:
        collection_info = get_ME("http://api-mainnet.magiceden.dev/v2/collections/{}".format(collection))
        collection_stats = get_ME("http://api-mainnet.magiceden.dev/v2/collections/{}/stats".format(collection))

        collection = {}
        collection['name'] = collection_info['name']
        collection['symbol'] = collection_info['symbol']
        collection['fp'] = convert_to_sol(collection_stats['floorPrice'])
        collection['ME_link'] = "https://magiceden.io/marketplace/{}".format(collection_info['symbol'])

        unique_collections_info.append(collection)

    nfts_owned = []

    for entry in data:
        if 'collection' not in entry:
            continue
        for collection in unique_collections_info:
            if entry['collection'] == collection['symbol']:
                nft = {}
                nft["nft_name"] = collection["name"]
                nft["floor_price"] = collection["fp"]
                nft["image_url"] = entry["image"]
                nft["ME_link"] = collection["ME_link"] 

                nfts_owned.append(nft)
            

    nfts_owned = sorted(nfts_owned, key=lambda k: k['floor_price'],reverse=True)

    min_portfolio_value = 0
    floor_prices = []

    for nft in nfts_owned:
        floor_prices.append(nft['floor_price'])

    min_portfolio_value = add_floor_prices(floor_prices)

    await ctx.channel.send ("**Minimum Portfolio Value:** {} SOL\n **The top 3 NFTs for wallet {} are:**\n".format(
        round(min_portfolio_value, 3),wallet))
    
    medals = [":first_place:",":second_place:",":third_place:"]
    place = 0
    
    for nft in nfts_owned:
        if place < 3:
            embed = Embed(
                title='{} **{}**'.format(medals[place], nft['nft_name']),
                url=nft['ME_link'])
            embed.set_image(url=nft["image_url"])
            await ctx.channel.send(embed=embed)
            place += 1
            
@bot.command()
async def collection(ctx, req):
    collection_info = get_ME("http://api-mainnet.magiceden.dev/v2/collections/{}".format(req))
    collection_stats = get_ME("http://api-mainnet.magiceden.dev/v2/collections/{}/stats".format(req))

    collection_name = collection_info['name']
    collection_description = collection_info['description']
    collection_image = collection_info['image']

    collection_fp = convert_to_sol(collection_stats['floorPrice'])
    active_listing = collection_stats['listedCount']

    response = "**{}**\n".format(collection_name) + translate("{}\n**Floor price:** {} SOL\n**Active listings:** {}\n{}\n".format(
        collection_description,collection_fp,active_listing,collection_image), ctx.channel.id)
    
    await ctx.channel.send(response)

@bot.command()
async def set_language(ctx, lang):
    for text_channel in ctx.guild.text_channels:
        channel_ID = int(text_channel.id)
        channel_name = str(text_channel.name)

        add_query = "INSERT INTO discord_channels (ch_ID, ch_Name, ch_Language) VALUES ({}, '{}', 'en')".format(
        channel_ID, channel_name)
        
        execute_query(conn, add_query)

    channels = execute_read_query(conn, "SELECT * FROM discord_channels")
    current_ch_id = int(ctx.channel.id)

    for channel in channels:
        if lang in languages:
                if channel['ch_ID'] == current_ch_id:
                    update_query = "UPDATE discord_channels SET ch_Language = '{}' WHERE ch_ID = {}".format(
                    lang, current_ch_id)
                    execute_query(conn, update_query)

                    await ctx.channel.send('{} has been set to {}'.format(channel['ch_Name'],lang))
                    break
        else:
            await ctx.channel.send('Not valid language')
            break

@bot.command()
async def set_roadmap(ctx, *, roadmap):
    channels = execute_read_query(conn, "SELECT * FROM discord_channels")

    for channel in channels:
        translated_roadmap = translate(roadmap, channel['ch_ID'])             
        update_query = "UPDATE discord_channels SET roadmap = '{}' WHERE ch_ID = {}".format(translated_roadmap, channel['ch_ID'])         
        execute_query(conn, update_query) 

@bot.command()
async def roadmap(ctx):
    channels = execute_read_query(conn, "SELECT * FROM discord_channels")
    current_ch_id = int(ctx.channel.id)

    for channel in channels:
        if channel['ch_ID'] == current_ch_id:
            await ctx.channel.send(channel['roadmap'])
            break

bot.run(token)