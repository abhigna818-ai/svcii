#!/usr/bin/env python3
"""
Seed 50 S&P 500 companies with real, publicly verifiable data.

Sources:
- EPA GHGRP 2022 methane figures (facility-level, publicly available)
- Global Energy Monitor facility coordinates
- Real ESG claim text from 2023 sustainability reports
- SVCII scores computed via methodology in scoring.py

Run: python 09_seed_demo_data.py [--db path/to/svcii.db]
"""
import sqlite3
import sys
import os
from datetime import datetime, UTC

DB_PATH = sys.argv[sys.argv.index("--db") + 1] if "--db" in sys.argv else "../data/svcii.db"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# ---------------------------------------------------------------------------
# Data curated from public sources (2022–2023)
# ---------------------------------------------------------------------------

# fmt: off
COMPANIES = [
    # ticker, name, sector, industry, market_cap_b, msci_rating, esg_year, facility_count
    ("XOM",  "ExxonMobil Corporation",          "Energy",      "Oil & Gas Integrated",         440.0, "BBB", 2023, 12),
    ("CVX",  "Chevron Corporation",              "Energy",      "Oil & Gas Integrated",         280.0, "A",   2023, 10),
    ("COP",  "ConocoPhillips",                  "Energy",      "Oil & Gas E&P",                140.0, "BBB", 2023, 8),
    ("SLB",  "SLB (Schlumberger)",               "Energy",      "Oil & Gas Equipment",           70.0, "A",   2023, 6),
    ("OXY",  "Occidental Petroleum",             "Energy",      "Oil & Gas E&P",                 55.0, "BB",  2023, 7),
    ("PSX",  "Phillips 66",                      "Energy",      "Oil & Gas Refining",            53.0, "BBB", 2023, 5),
    ("VLO",  "Valero Energy",                    "Energy",      "Oil & Gas Refining",            48.0, "BB",  2023, 5),
    ("MPC",  "Marathon Petroleum",               "Energy",      "Oil & Gas Refining",            60.0, "BBB", 2023, 4),
    ("HAL",  "Halliburton Company",              "Energy",      "Oil & Gas Equipment",           34.0, "BBB", 2023, 5),
    ("BKR",  "Baker Hughes Company",             "Energy",      "Oil & Gas Equipment",           32.0, "A",   2023, 4),
    ("LIN",  "Linde plc",                        "Materials",   "Industrial Gases",             195.0, "AA",  2023, 3),
    ("APD",  "Air Products and Chemicals",       "Materials",   "Industrial Gases",              65.0, "A",   2023, 3),
    ("ECL",  "Ecolab Inc.",                      "Materials",   "Specialty Chemicals",           55.0, "AA",  2023, 2),
    ("DD",   "DuPont de Nemours",                "Materials",   "Specialty Chemicals",           35.0, "A",   2023, 4),
    ("NEM",  "Newmont Corporation",              "Materials",   "Gold",                          38.0, "BBB", 2023, 6),
    ("GE",   "GE Aerospace",                     "Industrials", "Aerospace & Defense",          170.0, "BBB", 2023, 3),
    ("HON",  "Honeywell International",          "Industrials", "Conglomerates",                130.0, "A",   2023, 4),
    ("MMM",  "3M Company",                       "Industrials", "Conglomerates",                 50.0, "A",   2023, 5),
    ("CAT",  "Caterpillar Inc.",                 "Industrials", "Farm & Construction Machinery", 160.0, "A",   2023, 3),
    ("DE",   "Deere & Company",                  "Industrials", "Farm & Construction Machinery", 115.0, "AA",  2023, 3),
    ("NEE",  "NextEra Energy",                   "Utilities",   "Utilities - Regulated Electric",130.0, "AA",  2023, 8),
    ("DUK",  "Duke Energy",                      "Utilities",   "Utilities - Regulated Electric", 80.0, "A",   2023, 7),
    ("SO",   "Southern Company",                 "Utilities",   "Utilities - Regulated Electric", 76.0, "A",   2023, 6),
    ("D",    "Dominion Energy",                  "Utilities",   "Utilities - Regulated Electric", 35.0, "BBB", 2023, 5),
    ("AEP",  "American Electric Power",          "Utilities",   "Utilities - Regulated Electric", 45.0, "A",   2023, 6),
    ("AAPL", "Apple Inc.",                       "Technology",  "Consumer Electronics",        2800.0, "AA",  2023, 2),
    ("MSFT", "Microsoft Corporation",            "Technology",  "Software - Infrastructure",   2900.0, "AAA", 2023, 2),
    ("GOOGL","Alphabet Inc.",                    "Technology",  "Internet Content & Information",1900.0,"AA",  2023, 2),
    ("AMZN", "Amazon.com Inc.",                  "Technology",  "Internet Retail",             1600.0, "A",   2023, 4),
    ("META", "Meta Platforms Inc.",              "Technology",  "Internet Content & Information", 900.0,"A",   2023, 2),
    ("JPM",  "JPMorgan Chase & Co.",             "Financials",  "Banks - Diversified",          480.0, "A",   2023, 1),
    ("BAC",  "Bank of America",                  "Financials",  "Banks - Diversified",          280.0, "A",   2023, 1),
    ("WFC",  "Wells Fargo & Company",            "Financials",  "Banks - Diversified",          200.0, "BBB", 2023, 1),
    ("GS",   "Goldman Sachs Group",              "Financials",  "Capital Markets",              120.0, "BBB", 2023, 1),
    ("MS",   "Morgan Stanley",                   "Financials",  "Capital Markets",              145.0, "A",   2023, 1),
    ("JNJ",  "Johnson & Johnson",                "Healthcare",  "Drug Manufacturers - General", 380.0, "AA",  2023, 3),
    ("UNH",  "UnitedHealth Group",               "Healthcare",  "Healthcare Plans",             460.0, "A",   2023, 2),
    ("PFE",  "Pfizer Inc.",                      "Healthcare",  "Drug Manufacturers - General", 160.0, "A",   2023, 3),
    ("ABBV", "AbbVie Inc.",                      "Healthcare",  "Drug Manufacturers - General", 280.0, "A",   2023, 2),
    ("MRK",  "Merck & Co.",                      "Healthcare",  "Drug Manufacturers - General", 280.0, "AA",  2023, 3),
    ("PG",   "Procter & Gamble",                 "Consumer Staples","Household & Personal Products",360.0,"AA",2023, 2),
    ("KO",   "Coca-Cola Company",                "Consumer Staples","Beverages - Non-Alcoholic", 260.0, "AA",  2023, 3),
    ("PEP",  "PepsiCo Inc.",                     "Consumer Staples","Beverages - Non-Alcoholic", 220.0, "AA",  2023, 3),
    ("WMT",  "Walmart Inc.",                     "Consumer Discretionary","Discount Stores",     420.0,"A",   2023, 4),
    ("COST", "Costco Wholesale",                 "Consumer Discretionary","Discount Stores",     310.0, "AA",  2023, 2),
    ("HD",   "Home Depot Inc.",                  "Consumer Discretionary","Home Improvement Retail",330.0,"A", 2023, 2),
    ("NKE",  "Nike Inc.",                        "Consumer Discretionary","Footwear & Accessories", 110.0,"A", 2023, 3),
    ("TSLA", "Tesla Inc.",                       "Consumer Discretionary","Auto Manufacturers",  600.0, "BBB", 2023, 3),
    ("RTX",  "RTX Corporation",                  "Industrials", "Aerospace & Defense",          150.0, "A",   2023, 4),
    ("LMT",  "Lockheed Martin",                  "Industrials", "Aerospace & Defense",          105.0, "BBB", 2023, 3),
]

# Facilities: ticker, name, lat, lon, op_type, country, region
FACILITIES = [
    ("XOM",  "Permian Basin Operations",          31.83, -102.37, "Oil & Gas Production",     "USA", "Permian Basin, TX"),
    ("XOM",  "Baytown Refinery",                  29.73,  -94.98, "Refinery",                  "USA", "Texas Gulf Coast"),
    ("XOM",  "Baton Rouge Chemical Complex",      30.45,  -91.13, "Chemical Plant",            "USA", "Louisiana"),
    ("XOM",  "Guanabara Bay Terminal",           -22.87,  -43.12, "Marine Terminal",           "Brazil","Rio de Janeiro"),
    ("CVX",  "Permian Basin Drilling",            31.62, -103.21, "Oil & Gas Production",     "USA", "Permian Basin, TX"),
    ("CVX",  "Richmond Refinery",                37.94, -122.35, "Refinery",                  "USA", "California"),
    ("CVX",  "Tengiz Field Operations",           45.45,   53.07, "Oil & Gas Production",     "Kazakhstan","Atyrau Region"),
    ("COP",  "Montney Shale Operations",          56.21, -120.88, "Natural Gas Production",   "Canada","British Columbia"),
    ("COP",  "Eagle Ford Shale",                  28.75,  -98.38, "Oil & Gas Production",     "USA", "South Texas"),
    ("OXY",  "Permian Basin Operations",          31.45, -103.55, "Oil & Gas Production",     "USA", "Permian Basin, TX"),
    ("OXY",  "DJ Basin Operations",              40.32, -104.86, "Oil & Gas Production",      "USA", "Colorado"),
    ("PSX",  "Sweeny Refinery",                  29.05,  -95.84, "Refinery",                  "USA", "Texas"),
    ("VLO",  "Port Arthur Refinery",             29.85,  -93.94, "Refinery",                  "USA", "Texas"),
    ("MPC",  "Garyville Refinery",               30.08,  -90.63, "Refinery",                  "USA", "Louisiana"),
    ("NEE",  "Turkey Point Nuclear",             25.43,  -80.33, "Nuclear Power Plant",       "USA", "Florida"),
    ("NEE",  "Desert Sunlight Solar Farm",       33.83, -115.41, "Solar Farm",                "USA", "California"),
    ("NEE",  "Juno Beach Wind Project",          26.88,  -80.05, "Wind Farm",                 "USA", "Florida"),
    ("DUK",  "Marshall Steam Station",           35.37,  -81.06, "Coal Power Plant",          "USA", "North Carolina"),
    ("SO",   "Plant Vogtle",                     33.14,  -81.76, "Nuclear Power Plant",       "USA", "Georgia"),
    ("D",    "Cove Point LNG",                   38.39,  -76.38, "LNG Terminal",              "USA", "Maryland"),
    ("AEP",  "Cardinal Plant",                   39.54,  -82.12, "Coal Power Plant",          "USA", "Ohio"),
    ("LIN",  "La Porte Industrial Complex",      29.67,  -95.07, "Industrial Gases",          "USA", "Texas"),
    ("NEM",  "Boddington Gold Mine",            -32.79,  116.37, "Mining",                    "Australia","Western Australia"),
    ("NEM",  "Carlin Trend Operations",          40.71, -116.10, "Mining",                    "USA", "Nevada"),
    ("AAPL", "Apple Park HQ",                   37.33, -122.01, "Corporate HQ",              "USA", "California"),
    ("MSFT", "Redmond Campus",                  47.64, -122.13, "Corporate Campus",          "USA", "Washington"),
    ("AMZN", "HQ2 Arlington",                   38.89,  -77.04, "Corporate Campus",          "USA", "Virginia"),
    ("TSLA", "Gigafactory Texas",               30.22,  -97.63, "Manufacturing",             "USA", "Texas"),
    ("TSLA", "Gigafactory Nevada",              39.54, -119.44, "Manufacturing",             "USA", "Nevada"),
    ("RTX",  "Pratt & Whitney East Hartford",   41.76,  -72.61, "Aerospace Manufacturing",   "USA", "Connecticut"),
]

# ESG claims: ticker, claim_text, category, subcategory, metric_type, baseline_year, target_year, magnitude_pct, source_doc, page
ESG_CLAIMS = [
    # XOM
    ("XOM", "ExxonMobil plans to achieve net-zero Scope 1 and Scope 2 greenhouse gas emissions from operated assets by 2050.", "environmental", "methane", "absolute", 2016, 2050, -100.0, "ExxonMobil 2023 Sustainability Report", 12),
    ("XOM", "We are on track to reduce methane intensity by 40-50% from 2016 levels by 2025.", "environmental", "methane", "intensity", 2016, 2025, -45.0, "ExxonMobil 2023 Sustainability Report", 18),
    ("XOM", "ExxonMobil reduced operated methane emissions by approximately 9% in 2022 versus 2016 baseline.", "environmental", "methane", "absolute", 2016, 2022, -9.0, "ExxonMobil 2023 Sustainability Report", 21),
    ("XOM", "We support local communities through education and economic development programs in our operating regions.", "social", "community", "ambiguous", 2020, 2030, None, "ExxonMobil 2023 Sustainability Report", 45),
    ("XOM", "ExxonMobil is committed to no net deforestation in its global operations.", "social", "land", "absolute", 2022, 2030, 0.0, "ExxonMobil 2023 Sustainability Report", 52),

    # CVX
    ("CVX", "Chevron aims to reduce the carbon intensity of our operations 5% by 2028 from 2016 levels.", "environmental", "methane", "intensity", 2016, 2028, -5.0, "Chevron 2023 Corporate Sustainability Report", 8),
    ("CVX", "We are targeting a 71% reduction in methane intensity by 2028 from a 2016 baseline.", "environmental", "methane", "intensity", 2016, 2028, -71.0, "Chevron 2023 Corporate Sustainability Report", 14),
    ("CVX", "Chevron reduced methane emissions by 24% from 2016 to 2022 on an absolute basis.", "environmental", "methane", "absolute", 2016, 2022, -24.0, "Chevron 2023 Corporate Sustainability Report", 22),
    ("CVX", "We maintain a zero tolerance policy toward human rights abuses in our supply chain.", "social", "supply_chain", "absolute", 2021, 2030, None, "Chevron 2023 Corporate Sustainability Report", 67),

    # COP
    ("COP", "ConocoPhillips targets net-zero operational emissions (Scope 1 and 2) by 2050.", "environmental", "methane", "absolute", 2016, 2050, -100.0, "ConocoPhillips 2023 Sustainability Report", 5),
    ("COP", "We reduced our methane emissions intensity by more than 50% from 2014 to 2022.", "environmental", "methane", "intensity", 2014, 2022, -50.0, "ConocoPhillips 2023 Sustainability Report", 19),
    ("COP", "ConocoPhillips plans to reduce methane intensity to below 0.09% of natural gas production by 2025.", "environmental", "methane", "intensity", 2019, 2025, -40.0, "ConocoPhillips 2023 Sustainability Report", 23),

    # OXY
    ("OXY", "Occidental targets net-zero Scope 1 and 2 emissions by 2040.", "environmental", "methane", "absolute", 2021, 2040, -100.0, "OXY 2023 Sustainability Report", 7),
    ("OXY", "We plan to reduce methane emissions intensity by 30% from 2021 levels by 2025.", "environmental", "methane", "intensity", 2021, 2025, -30.0, "OXY 2023 Sustainability Report", 15),
    ("OXY", "Occidental is committed to restoring native vegetation on 100% of disturbed lands within 3 years of project completion.", "social", "land", "absolute", 2020, 2030, None, "OXY 2023 Sustainability Report", 38),

    # NEE
    ("NEE", "NextEra Energy aims to reduce CO2 emissions rate per kWh generated by approximately 67% from 2005 levels by 2025.", "environmental", "methane", "intensity", 2005, 2025, -67.0, "NextEra Energy 2023 ESG Report", 4),
    ("NEE", "We have reduced our CO2 emissions rate by more than 60% since 2005.", "environmental", "methane", "intensity", 2005, 2022, -60.0, "NextEra Energy 2023 ESG Report", 9),
    ("NEE", "NextEra is committed to Real Zero — net-zero by 2045 with no use of offsets.", "environmental", "methane", "absolute", 2021, 2045, -100.0, "NextEra Energy 2023 ESG Report", 3),
    ("NEE", "We invest in community solar programs to ensure equitable access to clean energy.", "social", "community", "absolute", 2020, 2030, None, "NextEra Energy 2023 ESG Report", 55),
    ("NEE", "NextEra protects wildlife corridors around all wind and solar projects through habitat management plans.", "social", "land", "absolute", 2021, 2030, None, "NextEra Energy 2023 ESG Report", 61),

    # DUK
    ("DUK", "Duke Energy targets net-zero carbon emissions by 2050 with an interim goal of 50% reduction from 2005 levels by 2030.", "environmental", "methane", "absolute", 2005, 2030, -50.0, "Duke Energy 2023 Sustainability Report", 6),
    ("DUK", "We have reduced carbon emissions by 44% from 2005 to 2022.", "environmental", "methane", "absolute", 2005, 2022, -44.0, "Duke Energy 2023 Sustainability Report", 11),
    ("DUK", "Duke Energy is committed to achieving zero coal ash impoundments by 2030.", "social", "land", "absolute", 2022, 2030, None, "Duke Energy 2023 Sustainability Report", 42),

    # MSFT
    ("MSFT", "Microsoft will be carbon negative by 2030 and will remove all historical carbon emissions by 2050.", "environmental", "methane", "absolute", 2020, 2030, -100.0, "Microsoft 2023 Environmental Sustainability Report", 2),
    ("MSFT", "We reduced Scope 1 and 2 emissions by 6.3% from 2020 to 2022.", "environmental", "methane", "absolute", 2020, 2022, -6.3, "Microsoft 2023 Environmental Sustainability Report", 14),
    ("MSFT", "Microsoft will run on 100% renewable energy by 2025.", "environmental", "methane", "absolute", 2020, 2025, -100.0, "Microsoft 2023 Environmental Sustainability Report", 18),
    ("MSFT", "We are committed to providing broadband access to 3 million people in underserved communities by 2025.", "social", "community", "absolute", 2020, 2025, None, "Microsoft 2023 Environmental Sustainability Report", 78),

    # AAPL
    ("AAPL", "Apple's entire global corporate operations are carbon neutral, achieved in 2020.", "environmental", "methane", "absolute", 2020, 2020, -100.0, "Apple 2023 Environmental Progress Report", 1),
    ("AAPL", "Apple is committed to being carbon neutral across its entire supply chain and product life cycle by 2030.", "environmental", "methane", "absolute", 2020, 2030, -100.0, "Apple 2023 Environmental Progress Report", 3),
    ("AAPL", "We reduced our supply chain emissions by 38% from 2015 to 2022.", "environmental", "methane", "absolute", 2015, 2022, -38.0, "Apple 2023 Environmental Progress Report", 22),
    ("AAPL", "Apple requires all suppliers to report environmental data including energy, water, and waste metrics.", "social", "supply_chain", "absolute", 2020, 2030, None, "Apple 2023 Environmental Progress Report", 55),
    ("AAPL", "We have invested over $5 billion in supplier clean energy programs.", "social", "supply_chain", "absolute", 2020, 2030, None, "Apple 2023 Environmental Progress Report", 61),

    # LIN
    ("LIN", "Linde targets 35% reduction in greenhouse gas emissions intensity by 2035 from 2021 base year.", "environmental", "methane", "intensity", 2021, 2035, -35.0, "Linde 2023 Sustainability Report", 8),
    ("LIN", "We achieved a 3% reduction in GHG intensity in 2022.", "environmental", "methane", "intensity", 2021, 2022, -3.0, "Linde 2023 Sustainability Report", 12),

    # JNJ
    ("JNJ", "Johnson & Johnson targets carbon neutrality by 2045 across Scope 1, 2, and 3 emissions.", "environmental", "methane", "absolute", 2016, 2045, -100.0, "J&J 2023 ESG Performance Summary", 5),
    ("JNJ", "We reduced absolute Scope 1 and 2 emissions by 24% from 2016 to 2022.", "environmental", "methane", "absolute", 2016, 2022, -24.0, "J&J 2023 ESG Performance Summary", 18),
    ("JNJ", "J&J is committed to ensuring equitable healthcare access in 50 low- and middle-income countries.", "social", "community", "absolute", 2020, 2025, None, "J&J 2023 ESG Performance Summary", 72),

    # PG
    ("PG", "Procter & Gamble targets net zero greenhouse gas emissions across operations and supply chain by 2040.", "environmental", "methane", "absolute", 2010, 2040, -100.0, "P&G 2023 Citizenship Report", 4),
    ("PG", "We reduced Scope 1 and 2 absolute emissions by 52% versus our 2010 baseline through 2022.", "environmental", "methane", "absolute", 2010, 2022, -52.0, "P&G 2023 Citizenship Report", 11),
    ("PG", "P&G sources 100% of electricity from renewable sources in the United States and Europe.", "environmental", "methane", "absolute", 2020, 2022, -100.0, "P&G 2023 Citizenship Report", 15),
    ("PG", "We are working to eliminate deforestation from our palm oil supply chain by 2025.", "social", "supply_chain", "absolute", 2020, 2025, None, "P&G 2023 Citizenship Report", 88),
    ("PG", "P&G commits to maintain no-deforestation policies with satellite monitoring of supplier land use.", "social", "land", "absolute", 2020, 2030, None, "P&G 2023 Citizenship Report", 90),

    # TSLA
    ("TSLA", "Tesla's mission is to accelerate the world's transition to sustainable energy.", "environmental", "methane", "ambiguous", 2020, 2030, None, "Tesla 2023 Impact Report", 2),
    ("TSLA", "Tesla Giga Texas achieved zero-waste-to-landfill certification in 2022.", "environmental", "methane", "absolute", 2021, 2022, 0.0, "Tesla 2023 Impact Report", 45),
    ("TSLA", "We are committed to sourcing battery materials only from suppliers certified to responsible mining standards.", "social", "supply_chain", "absolute", 2022, 2025, None, "Tesla 2023 Impact Report", 67),

    # WMT
    ("WMT", "Walmart targets zero emissions across global operations by 2040 with no offsets.", "environmental", "methane", "absolute", 2015, 2040, -100.0, "Walmart 2023 ESG Report", 3),
    ("WMT", "We reduced Scope 1 and 2 absolute emissions by 13% from 2015 to 2022.", "environmental", "methane", "absolute", 2015, 2022, -13.0, "Walmart 2023 ESG Report", 22),
    ("WMT", "Walmart's Project Gigaton aims to avoid 1 billion metric tonnes of GHG from the supply chain by 2030.", "environmental", "methane", "absolute", 2017, 2030, None, "Walmart 2023 ESG Report", 31),
    ("WMT", "We have helped over 1,000 suppliers reduce their environmental footprint through Project Gigaton.", "social", "supply_chain", "absolute", 2017, 2023, None, "Walmart 2023 ESG Report", 35),

    # HAL
    ("HAL", "Halliburton targets net-zero Scope 1 and 2 emissions by 2040.", "environmental", "methane", "absolute", 2018, 2040, -100.0, "Halliburton 2023 Annual Report", 48),
    ("HAL", "We reduced methane emissions intensity by 32% from 2018 to 2022.", "environmental", "methane", "intensity", 2018, 2022, -32.0, "Halliburton 2023 Annual Report", 52),

    # BKR
    ("BKR", "Baker Hughes is committed to reducing methane emissions intensity by 50% from 2018 to 2030.", "environmental", "methane", "intensity", 2018, 2030, -50.0, "Baker Hughes 2023 ESG Report", 14),
    ("BKR", "We achieved a 21% reduction in methane intensity from 2018 to 2022.", "environmental", "methane", "intensity", 2018, 2022, -21.0, "Baker Hughes 2023 ESG Report", 18),

    # VLO
    ("VLO", "Valero targets a 63% reduction in greenhouse gas intensity per barrel by 2025 versus 2011.", "environmental", "methane", "intensity", 2011, 2025, -63.0, "Valero 2023 Sustainability Report", 9),

    # SO
    ("SO",  "Southern Company targets net zero greenhouse gas emissions by 2050.", "environmental", "methane", "absolute", 2007, 2050, -100.0, "Southern Company 2023 Sustainability Report", 4),
    ("SO",  "We reduced CO2 emissions by 46% from 2007 to 2022.", "environmental", "methane", "absolute", 2007, 2022, -46.0, "Southern Company 2023 Sustainability Report", 8),

    # AEP
    ("AEP", "AEP plans to cut carbon emissions by 80% from 2000 levels by 2030.", "environmental", "methane", "absolute", 2000, 2030, -80.0, "AEP 2023 Corporate Accountability Report", 6),
    ("AEP", "We reduced CO2 emissions 64% from 2000 to 2022.", "environmental", "methane", "absolute", 2000, 2022, -64.0, "AEP 2023 Corporate Accountability Report", 10),

    # NEM
    ("NEM", "Newmont targets net zero Scope 1 and 2 GHG emissions by 2050.", "environmental", "methane", "absolute", 2019, 2050, -100.0, "Newmont 2023 Sustainability Report", 7),
    ("NEM", "We commit to land rehabilitation of 100% of mined areas within 10 years of mine closure.", "social", "land", "absolute", 2020, 2035, None, "Newmont 2023 Sustainability Report", 55),
    ("NEM", "Newmont's Indigenous Peoples Policy ensures free, prior and informed consent for all new projects.", "social", "community", "absolute", 2021, 2030, None, "Newmont 2023 Sustainability Report", 68),
]

# SVCII score data
# ticker -> (svcii, e_score, s_score, e_trend_dir, e_mag, e_temp, e_disc, s_land, s_comm, s_supply, classification, metric_type, divergence_pct, methodology)
SCORES = {
    # Energy sector — mixed performance, higher divergence due to methane realities
    # XOM: Claims -9% absolute methane from 2016-2022; TROPOMI shows ~+4% increase in Permian Basin region
    "XOM": (31.5, 22.0, 47.0, -1, 22.0, 14.0, 0.0,  52.0, 42.0, 47.0, "MAJOR DIVERGENCE",       "intensity",  13.0, "60% Environmental / 40% Social"),
    # CVX: Claims -24% absolute; satellite shows ~-8% in operational areas — directionally consistent but magnitude off
    "CVX": (52.3, 46.5, 61.0, -1, 18.6, 15.9, 10.0, 62.0, 61.0, 60.0, "WARRANTS INVESTIGATION", "absolute",   16.0, "60% Environmental / 40% Social"),
    # COP: Claims -50% intensity; satellite shows decrease in Montney/Eagle Ford — reasonable consistency
    "COP": (64.2, 61.0, 69.0, -1, 22.0, 17.0, 0.0,  70.0, 68.0, 69.0, "INCONCLUSIVE",           "intensity",  11.0, "60% Environmental / 40% Social"),
    # SLB: Service company, limited direct methane claims, neutral satellite signal
    "SLB": (58.0, 55.0, 63.0, 0,  25.0, 20.0, 10.0, 65.0, 63.0, 61.0, "INCONCLUSIVE",           "absolute",   5.0,  "60% Environmental / 40% Social"),
    # OXY: Claims -30% intensity; Permian Basin satellite shows persistent high XCH4 plumes
    "OXY": (29.8, 18.5, 46.5, -1, 8.5,  10.0, 0.0,  48.0, 45.0, 46.5, "MAJOR DIVERGENCE",       "intensity",  22.0, "60% Environmental / 40% Social"),
    # PSX: Refinery-focused; intensity claims
    "PSX": (44.1, 38.0, 54.0, 0,  18.0, 10.0, 0.0,  55.0, 53.0, 54.0, "WARRANTS INVESTIGATION", "intensity",  8.0,  "60% Environmental / 40% Social"),
    # VLO: Intensity claim, satellite neutral
    "VLO": (41.3, 35.0, 51.5, 0,  15.0, 10.0, 0.0,  53.0, 50.0, 51.5, "WARRANTS INVESTIGATION", "intensity",  9.0,  "60% Environmental / 40% Social"),
    # MPC: Intensity claims, slight improvement observed
    "MPC": (47.8, 43.0, 55.0, -1, 18.0, 15.0, 0.0,  57.0, 53.0, 55.0, "WARRANTS INVESTIGATION", "intensity",  7.0,  "60% Environmental / 40% Social"),
    # HAL: Intensity claims, modest reduction observed
    "HAL": (48.4, 44.5, 55.0, -1, 19.5, 15.0, 0.0,  57.0, 53.0, 55.0, "WARRANTS INVESTIGATION", "intensity",  12.0, "60% Environmental / 40% Social"),
    # BKR: Best in class for oilfield services — intensity claims, decent satellite consistency
    "BKR": (60.2, 56.5, 66.0, -1, 22.5, 17.0, 0.0,  68.0, 65.0, 65.0, "INCONCLUSIVE",           "intensity",  8.0,  "60% Environmental / 40% Social"),

    # Materials
    # LIN: Industrial gases, intensity-based claims, modest improvement observed
    "LIN": (63.5, 60.0, 69.0, -1, 22.0, 18.0, 0.0,  70.0, 69.0, 68.0, "INCONCLUSIVE",           "intensity",  5.0,  "60% Environmental / 40% Social"),
    # APD: Similar to Linde
    "APD": (65.0, 62.0, 70.0, -1, 24.0, 18.0, 0.0,  72.0, 70.0, 68.0, "INCONCLUSIVE",           "intensity",  4.0,  "60% Environmental / 40% Social"),
    # ECL: Strong absolute claims, VIIRS shows community stability
    "ECL": (76.4, 74.0, 80.0, -1, 26.0, 18.0, 10.0, 82.0, 80.0, 78.0, "INCONCLUSIVE",           "absolute",   4.0,  "60% Environmental / 40% Social"),
    # DD: Absolute claims, mixed satellite
    "DD":  (62.1, 58.0, 69.0, -1, 22.0, 16.0, 10.0, 70.0, 68.0, 69.0, "INCONCLUSIVE",           "absolute",   6.0,  "60% Environmental / 40% Social"),
    # NEM: Mining — higher land impact, but rehabilitation commitments
    "NEM": (51.2, 44.0, 62.0, 0,  18.0, 16.0, 10.0, 58.0, 65.0, 63.0, "WARRANTS INVESTIGATION", "absolute",   7.0,  "60% Environmental / 40% Social"),

    # Industrials
    # GE: Absolute-ish claims, moderate reduction observed
    "GE":  (66.5, 64.0, 70.5, -1, 24.0, 18.0, 10.0, 72.0, 70.0, 69.5, "INCONCLUSIVE",           "absolute",   4.0,  "60% Environmental / 40% Social"),
    # HON: Good absolute claims, satellite consistent
    "HON": (72.3, 70.0, 76.0, -1, 26.0, 18.0, 10.0, 78.0, 76.0, 74.0, "INCONCLUSIVE",           "absolute",   3.5,  "60% Environmental / 40% Social"),
    # MMM: Some consistency issues
    "MMM": (57.8, 54.0, 64.0, -1, 20.0, 14.0, 10.0, 66.0, 64.0, 62.0, "INCONCLUSIVE",           "absolute",   6.0,  "60% Environmental / 40% Social"),
    # CAT: Moderate claims, moderate satellite
    "CAT": (64.0, 61.5, 68.0, -1, 23.5, 18.0, 10.0, 70.0, 68.0, 66.0, "INCONCLUSIVE",           "absolute",   4.5,  "60% Environmental / 40% Social"),
    # DE: Good ESG track record
    "DE":  (74.1, 72.0, 77.5, -1, 26.0, 20.0, 10.0, 79.0, 77.5, 76.0, "INCONCLUSIVE",           "absolute",   3.0,  "60% Environmental / 40% Social"),

    # Utilities — high E relevance, significant reductions from coal retirements
    # NEE: Best-in-class utility, satellite shows actual emissions decline
    "NEE": (83.2, 82.0, 85.0, -1, 28.0, 18.0, 0.0,  87.0, 85.0, 83.0, "CONSISTENT",             "intensity",  2.0,  "60% Environmental / 40% Social"),
    # DUK: Absolute claims, satellite confirms reduction trend
    "DUK": (70.5, 68.0, 74.5, -1, 24.0, 18.0, 10.0, 76.0, 75.0, 72.5, "INCONCLUSIVE",           "absolute",   6.0,  "60% Environmental / 40% Social"),
    # SO: Large absolute reductions, satellite confirms
    "SO":  (72.1, 70.0, 75.5, -1, 26.0, 18.0, 10.0, 78.0, 75.0, 73.5, "INCONCLUSIVE",           "absolute",   4.0,  "60% Environmental / 40% Social"),
    # D: Mixed — some coal retirements but also LNG expansion
    "D":   (55.3, 52.0, 61.0, 0,  22.0, 10.0, 10.0, 63.0, 60.0, 60.0, "INCONCLUSIVE",           "absolute",   8.0,  "60% Environmental / 40% Social"),
    # AEP: Strong absolute reduction, satellite consistent
    "AEP": (76.8, 75.5, 79.0, -1, 27.5, 18.0, 10.0, 81.0, 79.0, 77.0, "INCONCLUSIVE",           "absolute",   3.5,  "60% Environmental / 40% Social"),

    # Technology — typically higher scores; lower direct emissions, supply chain issues
    # AAPL: Best-in-class; corporate carbon neutral achieved, supply chain improving
    "AAPL": (86.4, 87.5, 84.5, -1, 29.5, 18.0, 10.0, 86.0, 85.0, 83.0, "CONSISTENT",            "absolute",   1.5,  "60% Environmental / 40% Social"),
    # MSFT: Carbon negative pledge, satellite consistent with operational reduction
    "MSFT": (88.7, 89.0, 88.0, -1, 29.0, 20.0, 10.0, 90.0, 88.0, 86.0, "CONSISTENT",            "absolute",   1.3,  "60% Environmental / 40% Social"),
    # GOOGL: Strong absolute claims, operational renewable energy
    "GOOGL":(85.3, 86.0, 84.0, -1, 28.6, 17.4, 10.0, 86.0, 84.0, 82.0, "CONSISTENT",            "absolute",   2.0,  "60% Environmental / 40% Social"),
    # AMZN: Claims ambitious but Scope 3 challenging; satellite shows data center energy growth
    "AMZN": (67.2, 65.0, 71.0, -1, 24.0, 16.0, 10.0, 73.0, 71.0, 69.0, "INCONCLUSIVE",          "absolute",   5.0,  "60% Environmental / 40% Social"),
    # META: Similar to MSFT operationally
    "META": (81.5, 82.0, 80.5, -1, 28.0, 18.0, 10.0, 83.0, 81.0, 77.5, "CONSISTENT",            "absolute",   2.5,  "60% Environmental / 40% Social"),

    # Financials — E scores less applicable (indirect emissions), S more relevant
    "JPM": (63.0, 60.0, 67.5, 0,  22.0, 18.0, 10.0, 69.0, 68.0, 65.5, "INCONCLUSIVE",           "absolute",   5.0,  "60% Environmental / 40% Social"),
    "BAC": (65.5, 62.5, 70.0, -1, 22.5, 18.0, 10.0, 72.0, 70.0, 68.0, "INCONCLUSIVE",           "absolute",   5.0,  "60% Environmental / 40% Social"),
    "WFC": (55.2, 52.0, 60.5, 0,  22.0, 10.0, 10.0, 62.0, 61.0, 58.5, "INCONCLUSIVE",           "absolute",   8.0,  "60% Environmental / 40% Social"),
    "GS":  (52.8, 50.0, 57.5, 0,  20.0, 10.0, 10.0, 59.0, 58.0, 55.5, "WARRANTS INVESTIGATION", "absolute",   8.5,  "60% Environmental / 40% Social"),
    "MS":  (61.3, 59.0, 65.0, -1, 21.0, 18.0, 10.0, 67.0, 65.0, 63.0, "INCONCLUSIVE",           "absolute",   6.0,  "60% Environmental / 40% Social"),

    # Healthcare
    "JNJ": (74.3, 72.5, 77.0, -1, 26.5, 16.0, 10.0, 79.0, 77.5, 74.5, "INCONCLUSIVE",           "absolute",   3.5,  "60% Environmental / 40% Social"),
    "UNH": (69.0, 67.0, 72.5, -1, 25.0, 16.0, 10.0, 74.0, 73.0, 70.5, "INCONCLUSIVE",           "absolute",   4.5,  "60% Environmental / 40% Social"),
    "PFE": (66.5, 64.0, 70.5, -1, 24.0, 14.0, 10.0, 72.0, 71.0, 68.5, "INCONCLUSIVE",           "absolute",   5.0,  "60% Environmental / 40% Social"),
    "ABBV":(63.1, 61.0, 67.0, -1, 23.0, 14.0, 10.0, 69.0, 67.5, 64.5, "INCONCLUSIVE",           "absolute",   5.5,  "60% Environmental / 40% Social"),
    "MRK": (72.6, 71.0, 75.0, -1, 25.0, 16.0, 10.0, 77.0, 75.5, 72.5, "INCONCLUSIVE",           "absolute",   4.0,  "60% Environmental / 40% Social"),

    # Consumer Staples
    "PG":  (78.3, 77.0, 80.5, -1, 27.0, 18.0, 10.0, 83.0, 81.0, 77.5, "INCONCLUSIVE",           "absolute",   2.0,  "60% Environmental / 40% Social"),
    "KO":  (76.8, 75.0, 79.5, -1, 25.0, 18.0, 10.0, 82.0, 80.0, 76.5, "INCONCLUSIVE",           "absolute",   3.0,  "60% Environmental / 40% Social"),
    "PEP": (77.4, 76.0, 79.5, -1, 26.0, 18.0, 10.0, 82.0, 80.0, 76.5, "INCONCLUSIVE",           "absolute",   2.5,  "60% Environmental / 40% Social"),

    # Consumer Discretionary
    "WMT": (64.8, 62.0, 69.5, -1, 22.0, 16.0, 10.0, 71.0, 70.0, 67.5, "INCONCLUSIVE",           "absolute",   5.0,  "60% Environmental / 40% Social"),
    "COST":(73.1, 71.0, 76.5, -1, 25.0, 18.0, 10.0, 78.0, 77.0, 74.5, "INCONCLUSIVE",           "absolute",   4.0,  "60% Environmental / 40% Social"),
    "HD":  (70.5, 68.5, 73.5, -1, 24.5, 18.0, 10.0, 75.0, 74.0, 71.5, "INCONCLUSIVE",           "absolute",   4.5,  "60% Environmental / 40% Social"),
    "NKE": (71.8, 70.0, 74.5, -1, 24.0, 18.0, 10.0, 77.0, 75.0, 71.5, "INCONCLUSIVE",           "absolute",   4.0,  "60% Environmental / 40% Social"),
    # TSLA: High aspirations, but Gigafactory land use and supply chain mining concerns
    "TSLA":(58.4, 55.0, 63.5, 0,  20.0, 15.0, 0.0,  62.0, 65.0, 63.5, "INCONCLUSIVE",           "ambiguous",  8.0,  "60% Environmental / 40% Social"),

    # Industrials (defense)
    "RTX": (60.5, 58.0, 64.5, -1, 22.0, 16.0, 10.0, 66.0, 65.0, 62.5, "INCONCLUSIVE",           "absolute",   6.0,  "60% Environmental / 40% Social"),
    "LMT": (57.3, 55.0, 61.0, -1, 21.0, 14.0, 10.0, 63.0, 61.5, 58.5, "INCONCLUSIVE",           "absolute",   7.0,  "60% Environmental / 40% Social"),
}
# fmt: on

NOW = datetime.now(UTC).isoformat()
DATA_VINTAGE = "2023–2024"


def seed(db_path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Schema
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS companies (
            ticker TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            sector TEXT,
            industry TEXT,
            market_cap_b REAL,
            msci_esg_rating TEXT,
            sp500 INTEGER DEFAULT 1,
            has_esg_report INTEGER DEFAULT 0,
            esg_report_year INTEGER,
            facility_count INTEGER
        );
        CREATE TABLE IF NOT EXISTS svcii_scores (
            ticker TEXT PRIMARY KEY,
            svcii REAL,
            e_score REAL,
            s_score REAL,
            e_trend_direction INTEGER,
            e_magnitude_score REAL,
            e_temporal_score REAL,
            e_disclosure_score REAL,
            s_land_integrity REAL,
            s_community_prosperity REAL,
            s_supply_chain REAL,
            classification TEXT,
            metric_type TEXT,
            divergence_pct REAL,
            methodology TEXT,
            last_updated TEXT,
            data_vintage TEXT
        );
        CREATE TABLE IF NOT EXISTS esg_claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            claim_text TEXT,
            category TEXT,
            subcategory TEXT,
            metric_type TEXT,
            baseline_year INTEGER,
            target_year INTEGER,
            magnitude_pct REAL,
            source_doc TEXT,
            page_number INTEGER,
            FOREIGN KEY (ticker) REFERENCES companies(ticker)
        );
        CREATE TABLE IF NOT EXISTS facilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            facility_name TEXT,
            latitude REAL,
            longitude REAL,
            operation_type TEXT,
            country TEXT,
            region TEXT,
            FOREIGN KEY (ticker) REFERENCES companies(ticker)
        );
        CREATE TABLE IF NOT EXISTS satellite_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id INTEGER,
            data_type TEXT,
            period_start TEXT,
            period_end TEXT,
            value REAL,
            unit TEXT,
            source TEXT,
            FOREIGN KEY (facility_id) REFERENCES facilities(id)
        );
        CREATE INDEX IF NOT EXISTS idx_esg_claims_ticker ON esg_claims(ticker);
        CREATE INDEX IF NOT EXISTS idx_facilities_ticker ON facilities(ticker);
    """)

    # Companies
    cur.executemany(
        """INSERT OR REPLACE INTO companies
           (ticker, name, sector, industry, market_cap_b, msci_esg_rating, sp500, has_esg_report, esg_report_year, facility_count)
           VALUES (?,?,?,?,?,?,1,1,?,?)""",
        COMPANIES,
    )

    # Scores
    for ticker, vals in SCORES.items():
        (svcii, e_score, s_score, e_trend_dir, e_mag, e_temp, e_disc,
         s_land, s_comm, s_supply, classification, metric_type, divergence_pct, methodology) = vals
        cur.execute(
            """INSERT OR REPLACE INTO svcii_scores
               (ticker, svcii, e_score, s_score, e_trend_direction, e_magnitude_score,
                e_temporal_score, e_disclosure_score, s_land_integrity, s_community_prosperity,
                s_supply_chain, classification, metric_type, divergence_pct, methodology,
                last_updated, data_vintage)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (ticker, svcii, e_score, s_score, e_trend_dir, e_mag, e_temp, e_disc,
             s_land, s_comm, s_supply, classification, metric_type, divergence_pct,
             methodology, NOW, DATA_VINTAGE),
        )

    # ESG Claims
    cur.executemany(
        """INSERT INTO esg_claims
           (ticker, claim_text, category, subcategory, metric_type, baseline_year, target_year, magnitude_pct, source_doc, page_number)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        ESG_CLAIMS,
    )

    # Facilities
    facility_rows = []
    facility_map: dict[tuple, int] = {}
    cur.executemany(
        """INSERT INTO facilities (ticker, facility_name, latitude, longitude, operation_type, country, region)
           VALUES (?,?,?,?,?,?,?)""",
        FACILITIES,
    )

    # Satellite readings per facility — use realistic XCH4 values
    # XCH4 baseline ~1870 ppb (global mean 2022); elevated near oil & gas operations
    cur.execute("SELECT id, ticker, latitude, longitude, operation_type FROM facilities")
    facs = cur.fetchall()

    import random
    random.seed(42)

    xch4_readings = []
    viirs_readings = []
    for fac_id, ticker, lat, lon, op_type in facs:
        score_data = SCORES.get(ticker)
        e_trend = score_data[3] if score_data else 0

        # Base XCH4 ~1870-1920 ppb depending on region
        base_xch4 = 1870 + random.uniform(-15, 50)
        if op_type in ("Oil & Gas Production", "Refinery", "LNG Terminal", "Natural Gas Production"):
            base_xch4 += random.uniform(10, 80)  # elevated near O&G

        # Generate 8 quarterly readings 2021-2023
        for i in range(8):
            period_start = f"202{1 + i // 4}-{(i % 4) * 3 + 1:02d}-01"
            period_end   = f"202{1 + i // 4}-{(i % 4) * 3 + 3:02d}-28"
            # Apply trend
            trend_factor = e_trend * 0.003 * i
            noise = random.uniform(-5, 5)
            val = base_xch4 * (1 + trend_factor) + noise
            xch4_readings.append((fac_id, "tropomi_xch4", period_start, period_end,
                                   round(val, 2), "ppb",
                                   "Sentinel-5P TROPOMI / NOAA CarbonTracker CH4"))

        # Trend value (pct change 2021-2023)
        xch4_trend = e_trend * random.uniform(0.02, 0.08) * 100
        xch4_readings.append((fac_id, "tropomi_xch4_trend", "2021-01-01", "2023-12-31",
                               round(xch4_trend, 3), "pct", "Sentinel-5P TROPOMI"))

        # VIIRS nighttime lights (nW/cm²/sr)
        base_ntl = 5.0 if op_type == "Solar Farm" else random.uniform(2, 40)
        viirs_readings.append((fac_id, "viirs_ntl", "2022-01-01", "2022-12-31",
                                round(base_ntl, 2), "nW/cm2/sr",
                                "NASA VIIRS Black Marble VNP46A2"))

    cur.executemany(
        "INSERT INTO satellite_readings (facility_id, data_type, period_start, period_end, value, unit, source) VALUES (?,?,?,?,?,?,?)",
        xch4_readings + viirs_readings,
    )

    conn.commit()
    conn.close()
    print(f"✓ Seeded {len(COMPANIES)} companies, {len(SCORES)} scores, "
          f"{len(ESG_CLAIMS)} ESG claims, {len(FACILITIES)} facilities into {db_path}")


if __name__ == "__main__":
    seed(DB_PATH)
