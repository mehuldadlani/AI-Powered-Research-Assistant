import logging
from typing import Tuple, Any, Dict, List
from crewai import Task, Agent, Crew, LLM
import ollama
from src.config import Config

logger = logging.getLogger(__name__)

class CrewAIService:
    def __init__(self):
        self.model = Config.OLLAMA_MODEL
        self.llm = self.create_ollama_llm()

    async def initialize(self):
        logger.info("Initializing CrewAI service...")
        try:
            response = ollama.chat(model=self.model, messages=[{"role": "system", "content": "Test"}])
            logger.info(f"CrewAI service initialized successfully. Response: {response}")
        except Exception as e:
            logger.warning(f"Failed to initialize CrewAI service: {str(e)}")
            logger.info(f"Attempting to pull the model: {self.model}")
            try:
                ollama.pull(model=self.model)
                logger.info(f"Successfully pulled model {self.model}")
                response = ollama.chat(model=self.model, messages=[{"role": "system", "content": "Test"}])
                logger.info(f"CrewAI service initialized successfully after pulling the model. Response: {response}")
            except Exception as pull_error:
                logger.error(f"Failed to pull and initialize the model: {str(pull_error)}")
                raise RuntimeError(f"Failed to initialize CrewAI service: {str(pull_error)}")

    async def cleanup(self):
        logger.info("Cleaning up CrewAI service...")
        # Add any cleanup logic if needed
        logger.info("CrewAI service cleaned up")

    def create_ollama_llm(self):
        return LLM(
            model=f"ollama/{self.model}",
            base_url=Config.OLLAMA_BASE_URL,
        )

    async def analyze_with_crew(self, system_prompt: str, user_prompt: str) -> dict:
        try:
            analyst = Agent(
                role='Research Analyst',
                goal='Analyze and summarize research paper search results',
                backstory='You are an expert in analyzing academic literature and identifying key trends and insights.',
                allow_delegation=False,
                llm=self.create_ollama_llm(),
            )

            analysis_task = Task(
                description=f"{system_prompt}\n\nUser Query: {user_prompt}",
                agent=analyst,
                expected_output="A comprehensive analysis and answer to the user's query based on the given context."
            )

            crew = Crew(
                agents=[analyst],
                tasks=[analysis_task],
                verbose=Config.CREW_VERBOSE
            )

            logger.info("Starting CrewAI analysis process")
            result = crew.kickoff()
            logger.info("CrewAI analysis process completed")
            
            if hasattr(result, 'result'):
                return {"result": result.result}
            elif hasattr(result, 'task_output'):
                return {"result": result.task_output}
            else:
                return {"result": str(result)}
        except Exception as e:
            logger.exception(f"Error in CrewAI analysis process: {str(e)}")
            raise RuntimeError(f"Error in CrewAI analysis process: {str(e)}")

    async def create_agents(self) -> Tuple[Agent, Agent, Agent]:
        try:
            llm = self.create_ollama_llm()
            researcher = Agent(
                role='Researcher',
                goal='Thoroughly analyze research papers and extract key information',
                backstory='You are an expert researcher with years of experience in analyzing academic papers across various fields.',
                allow_delegation=False,
                llm=llm,
                model_name=self.model
            )
            
            writer = Agent(
                role='Technical Writer',
                goal='Create clear and concise summaries of research papers',
                backstory='You are a skilled technical writer specializing in transforming complex academic content into accessible summaries.',
                allow_delegation=False,
                llm=llm,
                model_name=self.model
            )
            
            editor = Agent(
                role='Editor',
                goal='Ensure the summary is accurate, well-structured, and tailored to the specified expertise level',
                backstory='You are an experienced editor with a keen eye for detail and a talent for adapting content to different audience levels.',
                allow_delegation=False,
                llm=llm,
                model_name=self.model
            )
            
            return researcher, writer, editor
        except Exception as e:
            logger.exception("Error creating agents")
            raise RuntimeError(f"Error creating agents: {str(e)}")


    async def summarize_with_crew(self, text: Any, level: str) -> Any:
        try:
            researcher, writer, editor = await self.create_agents()
            
            # Convert text to string if it's not already
            if not isinstance(text, str):
                text = str(text)
            
            # Truncate text safely
            truncated_text = text[:1000] if len(text) > 1000 else text
            
            research_task = Task(
                description=f"Analyze the following research paper and identify the key points, methodology, and findings:\n\n{truncated_text}...",
                agent=researcher,
                expected_output="A detailed analysis of the research paper's key points, methodology, and findings."
            )

            writing_task = Task(
                description=f"Using the analysis provided, create a summary of the research paper. Adjust the complexity based on the expertise level: {level}",
                agent=writer,
                expected_output=f"A clear and concise summary of the research paper, tailored to the {level} expertise level."
            )

            editing_task = Task(
                description=f"Review and refine the summary, ensuring it's appropriate for the {level} expertise level. Make any necessary adjustments for clarity and accuracy.",
                agent=editor,
                expected_output=f"A polished, accurate, and well-structured summary appropriate for the {level} expertise level."
            )

            crew = Crew(
                agents=[researcher, writer, editor],
                tasks=[research_task, writing_task, editing_task],
                verbose=Config.CREW_VERBOSE
            )

            logger.info(f"Starting CrewAI summarization process for level: {level}")
            result = crew.kickoff()
            logger.info("CrewAI summarization process completed")
            
            # Extract the summary from the CrewOutput object
            if hasattr(result, 'last_task_output'):
                return str(result.last_task_output)
            elif hasattr(result, 'task_output'):
                return str(result.task_output)
            else:
                return str(result)
        except Exception as e:
            logger.exception(f"Error in CrewAI summarization process: {str(e)}")
            raise RuntimeError(f"Error in CrewAI summarization process: {str(e)}")
        
    async def summarize_profile_with_crew(self, author_info: dict, level: str) -> str:
        try:
            llm = self.create_ollama_llm()
            
            profile_analyst = Agent(
                role='Academic Profile Analyst',
                goal='Provide a comprehensive and insightful analysis of academic researcher profiles',
                backstory="""You are a distinguished expert in analyzing academic profiles and research outputs. 
                With years of experience in bibliometrics and scientometrics, you excel at identifying key trends, 
                assessing research impact, and providing nuanced insights into a researcher's career trajectory.""",
                allow_delegation=False,
                llm=llm,
                model_name=self.model
            )

            recent_papers = self._format_paper_list(author_info.get('recent_papers', []))
            top_cited_papers = self._format_paper_list(author_info.get('top_cited', []))

            profile_summary_task = Task(
                description=f"""
                Conduct a thorough analysis of the following academic profile and provide a detailed, insightful summary:

                Author: {author_info['name']}
                Affiliation: {author_info['affiliation']}
                Total Publications: {len(author_info.get('publications', []))}
                Total Citations: {author_info.get('total_citations', 0)}
                
                Recent Papers (last 5):
                {recent_papers}
                
                Top Cited Papers (top 5):
                {top_cited_papers}

                Provide a comprehensive summary that addresses the following aspects:

                1. Research Focus and Expertise:
                - Identify and describe the main research areas the author specializes in.
                - Highlight any interdisciplinary aspects of their work.
                - Discuss the depth and breadth of their expertise based on their publication history.

                2. Key Contributions and Impact:
                - Analyze their most cited works and explain their significance to the field.
                - Discuss any groundbreaking or novel approaches introduced by the author.
                - Evaluate the overall impact of their research using citation metrics and the nature of their publications.

                3. Research Evolution and Trajectory:
                - Trace the evolution of their research interests over time.
                - Identify any shifts in focus or methodology throughout their career.
                - Discuss how their recent work builds upon or diverges from their earlier research.

                4. Collaboration and Academic Influence:
                - Highlight any notable collaborations or co-authorships.
                - Discuss the author's role in their research community (e.g., thought leader, pioneer in a specific area).
                - Mention any evident influence on other researchers or subfields.

                5. Future Research Directions:
                - Based on their recent work and research trends, predict potential future research directions.
                - Identify any emerging themes or technologies they might be moving towards.

                6. Academic Standing and Achievements:
                - Comment on their publication rate and the quality of venues they publish in.
                - Mention any awards, grants, or special recognitions, if available.
                - Provide context on how their work fits into broader academic or industry trends.

                7. Methodological Approaches:
                - Identify the primary research methodologies or techniques they employ.
                - Discuss any unique or innovative approaches they've developed or frequently use.

                Tailor the summary to a {level} level of expertise, ensuring that the language and depth of analysis 
                are appropriate for readers at that level. For a beginner level, focus on explaining concepts clearly 
                and avoiding jargon. For an expert level, delve into more technical details and nuanced analysis.

                Synthesize all this information into a coherent, well-structured narrative that gives a comprehensive 
                view of the researcher's profile, achievements, and potential future impact in their field.
                """,
                agent=profile_analyst ,
                expected_output="A comprehensive, well-structured analysis of the researcher's profile, including their main research areas, key contributions, impact, research evolution, collaborations, future directions, academic standing, and methodological approaches, tailored to the specified expertise level."
            )

            crew = Crew(
                agents=[profile_analyst],
                tasks=[profile_summary_task],
                verbose=Config.CREW_VERBOSE
            )

            result = crew.kickoff()
            
            if isinstance(result, str):
                return result
            elif hasattr(result, 'task_output'):
                return str(result.task_output)
            else:
                return str(result)

        except Exception as e:
            logger.exception(f"Error in CrewAI profile summarization: {str(e)}")
            raise RuntimeError(f"Error in CrewAI profile summarization: {str(e)}")



    def _format_paper_list(self, papers: List[Dict]) -> str:
        formatted_papers = []
        for paper in papers[:5]:  # Limit to top 5 papers for brevity
            title = paper.get('title', 'Unknown Title')
            citations = paper.get('num_citations', 'N/A')
            year = 'N/A'
            if 'bib' in paper:
                year = paper['bib'].get('pub_year', 'N/A')
            elif isinstance(paper, dict):
                year = paper.get('year', 'N/A')
            
            formatted_papers.append(f"- {title} (Citations: {citations}, Year: {year})")
        
        return "\n".join(formatted_papers)