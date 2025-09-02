#!/usr/bin/env python3
"""
Data quality verification script to show improvements
"""

import pandas as pd
import numpy as np

def analyze_data_quality(filepath, filename):
    """Analyze data quality of a CSV file"""
    print(f"\n{'='*60}")
    print(f"ANALYZING: {filename}")
    print(f"{'='*60}")
    
    df = pd.read_csv(filepath)
    print(f"Total records: {len(df)}")
    
    # Check for duplicates
    duplicate_count = df.duplicated().sum()
    print(f"Duplicate rows: {duplicate_count}")
    
    # Check for missing values
    print(f"\nMissing values:")
    missing_counts = df.isnull().sum()
    for col, count in missing_counts.items():
        if count > 0:
            percentage = (count / len(df)) * 100
            print(f"  {col}: {count} ({percentage:.1f}%)")
    
    # Check for empty strings
    print(f"\nEmpty string values:")
    for col in df.columns:
        if df[col].dtype == 'object':
            empty_count = (df[col] == '').sum()
            if empty_count > 0:
                percentage = (empty_count / len(df)) * 100
                print(f"  {col}: {empty_count} ({percentage:.1f}%)")
    
    # Location quality
    if 'location' in df.columns:
        valid_locations = df['location'].notna().sum()
        html_garbage = df['location'].astype(str).str.contains('a,abbr,acronym', na=False).sum()
        print(f"\nLocation quality:")
        print(f"  Valid locations: {valid_locations} ({valid_locations/len(df)*100:.1f}%)")
        print(f"  HTML garbage: {html_garbage} ({html_garbage/len(df)*100:.1f}%)")
    
    # Experience data
    if 'year_of_experience' in df.columns:
        valid_exp = df['year_of_experience'].notna().sum()
        print(f"\nExperience data:")
        print(f"  Valid experience: {valid_exp} ({valid_exp/len(df)*100:.1f}%)")
        if valid_exp > 0:
            exp_stats = df['year_of_experience'].describe()
            print(f"  Range: {exp_stats['min']:.0f}-{exp_stats['max']:.0f} years")
            print(f"  Average: {exp_stats['mean']:.1f} years")
    
    # Consultation fee
    if 'consultation_fee' in df.columns:
        valid_fees = df['consultation_fee'].notna().sum()
        zero_fees = (df['consultation_fee'] == 0).sum()
        print(f"\nConsultation fees:")
        print(f"  Valid fees: {valid_fees} ({valid_fees/len(df)*100:.1f}%)")
        print(f"  Zero fees: {zero_fees} ({zero_fees/len(df)*100:.1f}%)")
        if valid_fees > 0:
            fee_stats = df[df['consultation_fee'] > 0]['consultation_fee'].describe()
            print(f"  Range: ₹{fee_stats['min']:.0f}-₹{fee_stats['max']:.0f}")
            print(f"  Average: ₹{fee_stats['mean']:.0f}")
    
    # Doctor name duplicates
    if 'name' in df.columns:
        name_counts = df['name'].value_counts()
        duplicated_names = name_counts[name_counts > 1]
        print(f"\nDoctor duplicates:")
        print(f"  Unique doctors: {len(name_counts)} out of {len(df)} records")
        print(f"  Doctors with multiple entries: {len(duplicated_names)}")
        if len(duplicated_names) > 0:
            max_duplicates = duplicated_names.max()
            most_duplicated = duplicated_names.idxmax()
            print(f"  Most duplicated: {most_duplicated} ({max_duplicates} entries)")

def main():
    """Main comparison function"""
    print("DATA QUALITY COMPARISON")
    print("="*80)
    
    # Original files
    files_before = [
        ("/home/runner/work/medical_chatbot/medical_chatbot/medical_chatbot/src/Web_Scraping/practo_scraper/bangalore_enhanced.csv", "BEFORE: bangalore_enhanced.csv"),
        ("/home/runner/work/medical_chatbot/medical_chatbot/medical_chatbot/src/Web_Scraping/practo_scraper/data/cleaned_doctors_full.csv", "BEFORE: cleaned_doctors_full.csv")
    ]
    
    # Improved files
    files_after = [
        ("/home/runner/work/medical_chatbot/medical_chatbot/medical_chatbot/src/Web_Scraping/practo_scraper/data/consolidated_doctors_latest.csv", "AFTER: consolidated_doctors_latest.csv"),
        ("/home/runner/work/medical_chatbot/medical_chatbot/medical_chatbot/src/Web_Scraping/practo_scraper/data/bangalore_doctors_final.csv", "AFTER: bangalore_doctors_final.csv (Bangalore only)")
    ]
    
    # Analyze original files
    for filepath, filename in files_before:
        try:
            analyze_data_quality(filepath, filename)
        except Exception as e:
            print(f"Error analyzing {filename}: {e}")
    
    print("\n" + "="*80)
    print("AFTER IMPROVEMENTS")
    print("="*80)
    
    # Analyze improved files
    for filepath, filename in files_after:
        try:
            analyze_data_quality(filepath, filename)
        except Exception as e:
            print(f"Error analyzing {filename}: {e}")
    
    # Summary comparison
    print("\n" + "="*80)
    print("IMPROVEMENT SUMMARY")
    print("="*80)
    
    try:
        # Load data for comparison
        df_before1 = pd.read_csv(files_before[0][0])
        df_before2 = pd.read_csv(files_before[1][0])
        df_after = pd.read_csv(files_after[0][0])
        df_bangalore = pd.read_csv(files_after[1][0])
        
        total_before = len(df_before1) + len(df_before2)
        total_after = len(df_after)
        bangalore_after = len(df_bangalore)
        
        print(f"Records before: {total_before:,}")
        print(f"Records after (all cities): {total_after:,}")
        print(f"Records after (Bangalore only): {bangalore_after:,}")
        print(f"Duplicate reduction: {total_before - total_after:,} records ({(total_before - total_after)/total_before*100:.1f}%)")
        
        # Experience data improvement
        exp_before1 = df_before1['year_of_experience'].notna().sum()
        exp_before2 = df_before2['year_of_experience'].notna().sum()
        exp_after = df_bangalore['year_of_experience'].notna().sum()
        
        print(f"\nExperience data improvement:")
        print(f"  Before: {exp_before1 + exp_before2} records with experience")
        print(f"  After (Bangalore): {exp_after} records with experience")
        print(f"  Improvement: +{exp_after - (exp_before1 + exp_before2)} records")
        
        # Location data improvement
        loc_before1 = df_before1['location'].notna().sum()
        loc_before2 = df_before2['location'].notna().sum()
        loc_after = df_bangalore['location'].notna().sum()
        
        print(f"\nLocation data improvement:")
        print(f"  Before: {loc_before1 + loc_before2} records with location")
        print(f"  After (Bangalore): {loc_after} records with valid location")
        
        # HTML garbage reduction
        html_before1 = df_before1['location'].astype(str).str.contains('a,abbr,acronym', na=False).sum()
        html_before2 = df_before2['location'].astype(str).str.contains('a,abbr,acronym', na=False).sum()
        html_after = df_bangalore['location'].astype(str).str.contains('a,abbr,acronym', na=False).sum()
        
        print(f"\nHTML garbage reduction:")
        print(f"  Before: {html_before1 + html_before2} records with HTML garbage")
        print(f"  After (Bangalore): {html_after} records with HTML garbage")
        print(f"  Reduction: -{(html_before1 + html_before2) - html_after} records")
        
    except Exception as e:
        print(f"Error in summary calculation: {e}")

if __name__ == "__main__":
    main()