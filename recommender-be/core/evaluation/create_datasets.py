import logging
from typing import List, Any, Dict
from langfuse import Langfuse
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_datasets():
    try:
        langfuse = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST
        )

        if langfuse:
            # Create metric evaluation dataset
            logger.info("Generating metric evaluation dataset...")
            metric_dataset = generate_metric_evaluation_dataset()
            logger.info(f"Generated {len(metric_dataset)} metric evaluation examples.")

            logger.info("Creating/updating metric evaluation dataset in Langfuse...")
            metric_langfuse_dataset = create_or_update_langfuse_dataset(
                langfuse,
                "movie_recommendation_metric_eval",
                "Evaluation dataset for movie recommendation metrics",
                metric_dataset
            )
            if metric_langfuse_dataset:
                logger.info('Metric evaluation dataset created/updated successfully in Langfuse.')
            else:
                logger.warning('Failed to create/update metric evaluation dataset in Langfuse.')

            # Create complex evaluation dataset
            logger.info("Generating complex evaluation dataset...")
            complex_dataset = generate_complex_evaluation_dataset()
            logger.info(f"Generated {len(complex_dataset)} complex evaluation examples.")

            logger.info("Creating/updating complex evaluation dataset in Langfuse...")
            complex_langfuse_dataset = create_or_update_langfuse_dataset(
                langfuse,
                "movie_recommendation_complex_eval",
                "Complex evaluation dataset for movie recommendations",
                complex_dataset
            )
            if complex_langfuse_dataset:
                logger.info('Complex evaluation dataset created/updated successfully in Langfuse.')
            else:
                logger.warning('Failed to create/update complex evaluation dataset in Langfuse.')
        else:
            logger.error('Langfuse client is not configured. Unable to create datasets.')
    except Exception as e:
        logger.error(f"An error occurred while creating datasets: {str(e)}", exc_info=True)

def generate_metric_evaluation_dataset() -> List[Dict[str, Any]]:
    return [
        {
            "query": "Recommend some science fiction movies",
            "expected_movies": ["Inception", "Interstellar", "The Matrix", "Blade Runner", "Ex Machina"],
            "expected_response": "Based on your interest in science fiction movies, I would recommend the following films:\n\n1. Inception (2010) - A mind-bending sci-fi thriller directed by Christopher Nolan.\n2. Interstellar (2014) - An epic space adventure that explores concepts of time and gravity.\n3. The Matrix (1999) - A groundbreaking cyberpunk film about reality and artificial intelligence.\n4. Blade Runner (1982) - A neo-noir sci-fi classic set in a dystopian future.\n5. Ex Machina (2014) - A thought-provoking exploration of artificial intelligence and consciousness."
        },
        {
            "query": "What are some good action movies from the 90s?",
            "expected_movies": ["Terminator 2: Judgment Day", "The Matrix", "Die Hard: With a Vengeance", "Speed", "Mission: Impossible"],
            "expected_response": "Here are some excellent action movies from the 1990s:\n\n1. Terminator 2: Judgment Day (1991) - A groundbreaking sequel with amazing special effects and intense action sequences.\n2. The Matrix (1999) - A sci-fi action film that revolutionized the genre with its innovative visual effects and compelling story.\n3. Die Hard: With a Vengeance (1995) - The third installment in the Die Hard series, featuring Bruce Willis in his iconic role as John McClane.\n4. Speed (1994) - A high-octane thriller starring Keanu Reeves and Sandra Bullock on a bus that can't slow down.\n5. Mission: Impossible (1996) - The first movie in the long-running spy franchise, starring Tom Cruise as Ethan Hunt."
        },
        {
            "query": "Recommend some classic comedies",
            "expected_movies": ["Airplane!", "Ghostbusters", "The Big Lebowski", "Groundhog Day", "Monty Python and the Holy Grail"],
            "expected_response": "Here are some classic comedies that have stood the test of time:\n\n1. Airplane! (1980) - A hilarious spoof of disaster movies filled with slapstick humor and memorable one-liners.\n2. Ghostbusters (1984) - A supernatural comedy that blends humor with action and special effects.\n3. The Big Lebowski (1998) - A cult classic from the Coen brothers, known for its quirky characters and quotable dialogue.\n4. Groundhog Day (1993) - Bill Murray stars in this clever comedy about a man living the same day over and over.\n5. Monty Python and the Holy Grail (1975) - A surreal and absurdist take on Arthurian legend from the Monty Python comedy troupe."
        }
    ]

def generate_complex_evaluation_dataset() -> List[Dict[str, str]]:
    return [
        {
            "query": "Can you list all the movies directed by Christopher Nolan along with their release dates and popularity?",
            "expected_response": "Here's a list of movies directed by Christopher Nolan, along with their release dates and popularity scores:\n\n1. **Inception** (2010) - Popularity: 29.1\n2. **Interstellar** (2014) - Popularity: 32.2\n3. **The Dark Knight** (2008) - Popularity: 123.167\n4. **The Dark Knight Rises** (2012) - Popularity: 53.416\n5. **Batman Begins** (2005) - Popularity: 38.883\n\nNote: This list includes only a sample of Nolan's films from the available dataset. Popularity scores are based on the data provided and may not reflect current popularity."
        },
        {
            "query": "What is the average budget of movies directed by Christopher Nolan, and how does it compare to the average budget of all movies?",
            "expected_response": "Based on the available data:\n\n1. Average budget of Christopher Nolan's movies: $176.8 million\n2. Average budget of all movies in the dataset: $42.3 million\n\nChristopher Nolan's average movie budget is approximately 4.18 times higher than the average budget of all movies in the dataset. This significant difference reflects Nolan's status as a high-profile director known for large-scale, visually ambitious projects."
        },
        {
            "query": "Among the top 10 most popular movies directed by Christopher Nolan, which ones had the lowest budget-to-popularity ratio?",
            "expected_response": "After analyzing Christopher Nolan's top 10 most popular movies, here are the three with the lowest budget-to-popularity ratio:\n\n1. **The Dark Knight** (2008)\n   - Budget: $185 million\n   - Popularity: 123.167\n   - Budget-to-popularity ratio: 1.50\n\n2. **Inception** (2010)\n   - Budget: $160 million\n   - Popularity: 29.1\n   - Budget-to-popularity ratio: 5.50\n\n3. **The Dark Knight Rises** (2012)\n   - Budget: $250 million\n   - Popularity: 53.416\n   - Budget-to-popularity ratio: 4.68\n\nThese films demonstrate Nolan's ability to create highly popular movies with relatively efficient budget utilization."
        },
        {
            "query": "How does Christopher Nolan's average movie runtime compare with other directors in the action genre?",
            "expected_response": "After analyzing the data:\n\n1. Christopher Nolan's average movie runtime (action genre): 152 minutes\n2. Average runtime of action movies by other directors: 126 minutes\n\nChristopher Nolan's action movies are, on average, 26 minutes (or about 20.6%) longer than the typical action movie in our dataset. This aligns with Nolan's reputation for creating epic, complex narratives that often require longer runtimes to fully develop."
        },
        {
            "query": "For each decade, what are the top 3 highest-grossing movies directed by Christopher Nolan, and what was the average crew size for each of these movies?",
            "expected_response": "Here's the breakdown by decade:\n\n2000s:\n1. **The Dark Knight** (2008)\n   - Gross: $1,004,558,444\n   - Average crew size: 728\n2. **Batman Begins** (2005)\n   - Gross: $374,218,673\n   - Average crew size: 645\n3. **The Prestige** (2006)\n   - Gross: $109,676,311\n   - Average crew size: 412\n\n2010s:\n1. **The Dark Knight Rises** (2012)\n   - Gross: $1,084,939,099\n   - Average crew size: 810\n2. **Inception** (2010)\n   - Gross: $836,836,967\n   - Average crew size: 753\n3. **Interstellar** (2014)\n   - Gross: $701,729,206\n   - Average crew size: 789\n\nNote: Crew size data is approximate and based on available information in the dataset."
        },
        {
            "query": "Which actors appear most frequently in action movies?",
            "expected_response": "Based on our dataset, here are the top 5 actors who appear most frequently in action movies:\n\n1. Bruce Willis - 12 appearances\n2. Jason Statham - 10 appearances\n3. Sylvester Stallone - 9 appearances\n4. Vin Diesel - 8 appearances\n5. Dwayne Johnson - 7 appearances\n\nThese actors are known for their roles in action films, which explains their frequent appearances in this genre."
        },
        {
            "query": "Who are the top 5 highest-paid actors in comedy movies, and which of their movies had the highest popularity?",
            "expected_response": "Here are the top 5 highest-paid actors in comedy movies and their most popular comedy film:\n\n1. Adam Sandler\n   - Highest popularity: **Grown Ups** (2010) - Popularity: 27.593\n\n2. Will Ferrell\n   - Highest popularity: **The Other Guys** (2010) - Popularity: 17.097\n\n3. Ben Stiller\n   - Highest popularity: **Night at the Museum** (2006) - Popularity: 24.797\n\n4. Owen Wilson\n   - Highest popularity: **Wedding Crashers** (2005) - Popularity: 18.372\n\n5. Vince Vaughn\n   - Highest popularity: **Wedding Crashers** (2005) - Popularity: 18.372\n\nNote: Salary information is based on reported figures and may not reflect exact earnings. Popularity scores are from the dataset and may not represent current popularity."
        },
        {
            "query": "What is the relationship between the number of leading roles an actor takes in drama movies and the movie's average rating over time?",
            "expected_response": "After analyzing the data, we've found the following relationship between the number of leading roles in drama movies and average movie ratings:\n\n1. Actors with 1-3 leading roles: Average rating of 6.7\n2. Actors with 4-6 leading roles: Average rating of 7.1\n3. Actors with 7-10 leading roles: Average rating of 7.4\n4. Actors with more than 10 leading roles: Average rating of 7.8\n\nThere appears to be a positive correlation between the number of leading roles an actor takes in drama movies and the average rating of those movies. This could suggest that actors who consistently take leading roles in dramas tend to choose higher-quality projects or improve their performances over time."
        },
        {
            "query": "Which actors have appeared in the most diverse range of genres, and how does their genre versatility impact the movie's success in terms of both popularity and profitability?",
            "expected_response": "After analyzing the data, here are the top 5 actors with the most diverse range of genres and the impact of their versatility:\n\n1. Johnny Depp (8 genres)\n   - Average popularity: 32.5\n   - Average profitability ratio: 2.8\n\n2. Brad Pitt (7 genres)\n   - Average popularity: 28.7\n   - Average profitability ratio: 3.1\n\n3. Tom Hanks (7 genres)\n   - Average popularity: 30.2\n   - Average profitability ratio: 3.5\n\n4. Meryl Streep (7 genres)\n   - Average popularity: 25.9\n   - Average profitability ratio: 2.9\n\n5. Leonardo DiCaprio (6 genres)\n   - Average popularity: 35.1\n   - Average profitability ratio: 3.3\n\nIn general, actors with higher genre versatility tend to have higher average popularity scores and profitability ratios. This suggests that versatility can contribute to both commercial success and audience engagement across different types of films."
        },
        {
            "query": "For each genre, what is the trend in the average number of cast members over the last 20 years, and how does this correlate with the movie's budget and revenue?",
            "expected_response": "Here's an analysis of the trends in average cast size by genre over the last 20 years and their correlation with budget and revenue:\n\n1. Action:\n   - Cast size trend: Increased by 15%\n   - Budget correlation: Strong positive (0.75)\n   - Revenue correlation: Moderate positive (0.62)\n\n2. Comedy:\n   - Cast size trend: Increased by 8%\n   - Budget correlation: Weak positive (0.35)\n   - Revenue correlation: Weak positive (0.28)\n\n3. Drama:\n   - Cast size trend: Decreased by 5%\n   - Budget correlation: Weak negative (-0.22)\n   - Revenue correlation: No significant correlation (0.05)\n\n4. Sci-Fi:\n   - Cast size trend: Increased by 22%\n   - Budget correlation: Strong positive (0.82)\n   - Revenue correlation: Strong positive (0.78)\n\n5. Horror:\n   - Cast size trend: Increased by 3%\n   - Budget correlation: Weak positive (0.18)\n   - Revenue correlation: No significant correlation (0.09)\n\nIn general, genres like Action and Sci-Fi show a trend of increasing cast sizes, which strongly correlates with higher budgets and revenues. Dramas, on the other hand, have seen a slight decrease in cast size with little correlation to budget or revenue. Comedies and Horror films show minimal changes in cast size and weak correlations with financial aspects."
        }
    ]

def create_or_update_langfuse_dataset(langfuse: Langfuse, dataset_name: str, description: str, data: List[Dict[str, str]]) -> Any:
    if not langfuse:
        logger.warning("Langfuse client is not configured. Skipping dataset creation/update.")
        return None

    try:
        # Create or update the dataset
        dataset = langfuse.create_dataset(name=dataset_name)
        
        # Add new examples
        for item in data:
            langfuse.create_dataset_item(
                dataset_name=dataset_name,
                input={"query": item["query"]},
                expected_output=item["expected_response"]
            )

        logger.info(f"Created/Updated Langfuse dataset: {dataset_name}")
        return dataset
    except Exception as e:
        logger.error(f"Error creating/updating dataset {dataset_name}: {str(e)}", exc_info=True)
        return None

if __name__ == "__main__":
    create_datasets()
