##  <img src="https://media.tenor.com/Wq-8a2yGCSkAAAAi/stethoscope-stethoscope-images.gif" width="48" height="48"> Doctor Fee Prediction


This project aims to create a web interface that allows users to predict doctor consultation fees based on their input. The machine learning model was trained on a dataset obtained by scraping data from the Practo website using Selenium. With the use of Python Pandas, the scraped data was thoroughly cleaned & preprocessed for accurate predictions.
##  <img src="https://user-images.githubusercontent.com/106439762/181935629-b3c47bd3-77fb-4431-a11c-ff8ba0942b63.gif" width="48" height="48"> **User's Manual**

| Files/Folder| Description |
| ------------- | ------------- |
| **Dataset Folder** | This folder provides data state wise in csv format |
| **Python File** | This contains the .ipynb file of the analysis for Data Extract, Data cleaning, EDA and ML Models.  |
| **HTML File** | This contains the .html file for User Interface.  |

<br>

<p align="center"><img src="https://images.unsplash.com/photo-1584982751601-97dcc096659c?q=80&w=2072&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D" width="400" ></p>

   
## Findings from the Doctor Fee Prediction Project 🧪

- According to the Practo dataset, Bangalore has the highest number of doctors.

<img src="https://github.com/Vishwanath-J-25/Doctor-Fee-Prediction-Model/blob/main/githu/Screenshot%20(493).png" width="700" >

 
- The most common degrees among doctors are MBBS, MD, and BDS, with the highest representation in the dataset.
  
<img src="https://github.com/Vishwanath-J-25/Doctor-Fee-Prediction-Model/blob/main/githu/Screenshot%20(492).png" width="800" >

  
- The dataset indicates that the three most prominent specialties among doctors are:
  - Dentist
  - Gynecologist
  - Pediatrician

<img src="https://github.com/Vishwanath-J-25/Doctor-Fee-Prediction-Model/blob/main/githu/Screenshot%20(494).png" width="800" >


        
 <br>


## 🏥 Doctor Fee Prediction ML Model Creation Steps 🧠

<img src="https://github.com/Sannidhi-Shetty2/Doctor-Fee-Prediction/assets/62684303/b5ff0161-b645-4677-80f8-5520e5ecf3d9" width="800" >

**1. Data Collection:** Gathered doctor-related information from Practo using web scraping techniques with Selenium.

**2. Data Preprocessing:** Conducted thorough data cleaning, handling missing values, and transforming categorical variables into numerical representations.

**3. Feature Engineering:** Derived additional relevant features from the existing dataset, such as extracting qualifications.

**4. Model Selection:** Explored various regression algorithms and selected potential candidates based on initial performance evaluation.

**5. Hyperparameter Tuning:** Utilized GridSearchCV to fine-tune hyperparameters for each selected model, optimizing their performance.

**6. Model Training:** Trained multiple models on the dataset with the tuned hyperparameters to improve predictive accuracy.

**7. Weighted Voting:** Implemented a Weighted Voting technique, combining predictions from multiple models, each with a specific weight.

**8. Model Evaluation:** Evaluated the ensemble model using appropriate metrics such as Mean Absolute Error (MAE) or Root Mean Squared Error (RMSE) to measure prediction accuracy.

**9. Web App Development:** Developed a user-friendly web application using Flask, HTML, and CSS to offer an intuitive interface for users to input parameters.

## 🏥 Doctor Fee Prediction Web application

 <p align="center"><img src="https://github.com/Sannidhi-Shetty2/Doctor-Fee-Prediction/assets/62684303/92d53380-68d4-4289-8d43-4e386d3b2025" width="500" ></p>

## 🏥 Challenges and Learnings

**1. Data Extraction:** We intially faced difficulties to get the data from the server,as
we had to explore it, and tried to figure it out.. 

**2. Model Selection:**  Explored different ML models to identify the Best models.

**3. Hyperparameter Tunning:**  Hyperparameter tuning was time-consuming due to limited time for model development

**4. Creating the webpage:**  As we are new to this concept, this was quiet challenging and
interesting in creating it.

 
## 🏥 Conclusion

**1. Healthcare Accessibility:** By giving patients an idea of potential costs, it helps them seek appropriate medical care without the barrier of uncertainty about fees.

**2. Transparency and Trust:**  Clear fee estimates foster trust and confidence in medical services, enhancing the doctor-patient relationship.

**3. Efficiency for Providers:** With fee estimates readily available, administrative processes become smoother, leading to improved overall service efficiency.
