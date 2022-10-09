from scrape_jsic import JSICDefinitionExtractor

if __name__ == "__main__":
    jsic_extractor = JSICDefinitionExtractor()
    jsic_extractor.get_jsic_code()

    for classification in ["division", "major_group", "detail"]:
        df = jsic_extractor.get_jsic_definition(classification)
        df.to_csv(f"data/jsic_{classification}.csv", index=False)
