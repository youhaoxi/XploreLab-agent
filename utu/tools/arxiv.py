""" 
camel/toolkits/arxiv_toolkit.py
https://info.arxiv.org/help/api/index.html
"""

import logging
from typing import Generator, List, Optional, Dict, Callable

import arxiv

from .base import AsyncBaseToolkit
from ..config import ToolkitConfig


logger = logging.getLogger("utu")


class ArxivToolkit(AsyncBaseToolkit):
    def __init__(self, config: ToolkitConfig = None, activated_tools: list[str] = None) -> None:
        super().__init__(config, activated_tools)
        self.client = arxiv.Client()

    def _get_search_results(
        self,
        query: str,
        paper_ids: Optional[List[str]] = None,
        max_results: Optional[int] = 5,
    ) -> Generator[arxiv.Result, None, None]:
        paper_ids = paper_ids or []
        search_query = arxiv.Search(
            query=query,
            id_list=paper_ids,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,      # TODO: configurable, support advanced search
        )
        return self.client.results(search_query)

    async def search_papers(
        self,
        query: str,
        paper_ids: Optional[List[str]] = None,
        max_results: Optional[int] = 5,
    ) -> List[Dict[str, str]]:
        r"""Searches for academic papers on arXiv using a query string and optional paper IDs.

        Args:
            query (str): The search query string.
            paper_ids (List[str], optional): A list of specific arXiv paper IDs to search for. (default: :obj:`None`)
            max_results (int, optional): The maximum number of search results to return. (default: :obj:`5`)

        Returns:
            List[Dict[str, str]]: A list of dictionaries, each containing information about a paper, including title, published date, authors, entry ID, summary.
        """
        search_results = self._get_search_results(
            query, paper_ids, max_results
        )
        papers_data = []

        for paper in search_results:
            paper_info = {
                "title": paper.title,
                "published_date": paper.updated.date().isoformat(),
                "authors": [author.name for author in paper.authors],
                "entry_id": paper.entry_id,
                "summary": paper.summary,
                "pdf_url": paper.pdf_url,
            }

            # # Extract text from the paper
            # try:
            #     # TODO: Use chunkr instead of atxiv_to_text for better performance and reliability
            #     # from arxiv2text import arxiv_to_text
            #     # text = arxiv_to_text(paper_info["pdf_url"])
            # except Exception as e:
            #     logger.error(
            #         "Failed to extract text content from the PDF at "
            #         "the specified URL. "
            #         f"URL: {paper_info.get('pdf_url', 'Unknown')} | Error: {e}"
            #     )
            #     text = ""
            # paper_info['paper_text'] = text
            papers_data.append(paper_info)
        return papers_data

    async def download_papers(
        self,
        query: str,
        paper_ids: Optional[List[str]] = None,
        max_results: Optional[int] = 5,
        output_dir: Optional[str] = "./",
    ) -> str:
        r"""Downloads PDFs of academic papers from arXiv based on the provided query.

        Args:
            query (str): The search query string.
            paper_ids (List[str], optional): A list of specific arXiv paper IDs to download. (default: :obj:`None`)
            max_results (int, optional): The maximum number of search results to download. (default: :obj:`5`)
            output_dir (str, optional): The directory to save the downloaded PDFs. Defaults to the current directory.

        Returns:
            str: Status message indicating success or failure.
        """
        try:
            search_results = self._get_search_results(
                query, paper_ids, max_results
            )

            for paper in search_results:
                paper.download_pdf(
                    dirpath=output_dir, filename=f"{paper.title}" + ".pdf"
                )
            return "papers downloaded successfully"
        except Exception as e:
            return f"An error occurred: {e}"

    async def get_tools_map(self) -> dict[str, Callable]:
        return {
            "search_papers": self.search_papers,
            "download_papers": self.download_papers,
        }