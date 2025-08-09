# Contributing

Before contributing to this repository, please first discuss the change you wish to make via an issue. We want to make sure that your contribution aligns with the goals of the project before you begin working on it.

## Reporting Issues/Asking Questions
> We assume that you have read the available documentation before reporting any issues or asking any questions.

Please follow these steps when reporting an issue or asking a question:
- Ensure you are using the latest version.
- Search through open issues to ensure it's not a duplicate.
- Describe the issue clearly with steps to reproduce it, if possible.
- Provide all relevant input values (e.g., Spotify playlist links) and the output results.
- Use suitable and clear formatting, such as code blocks, headings, and bullet points.
- In general, provide as much context as possible about the issue or question.

We appreciate your help in improving the project and making the issue resolution process smoother!

## How to Contribute Code
1. Fork the repository.
2. Create a new branch for your changes: `git checkout -b featurename`.
3. Ensure your code complies with the existing style:
    - Passes `flake8` linting
    - Passes `mypy` type checking
4. Ensure the output result is 100% identical to the original output.
5. Ensure it **does not overcomplicate the tool** or introduce unnecessary dependencies.
6. Ensure your changes do not break any existing functionality.
7. Submit a pull request with a detailed description of what was added or fixed. If necessary, provide detailed documentations.

## Scope of Project
- This project is focused solely on providing a tool to download music from Spotify playlists.
- This project aims to follow the [KISS](https://en.wikipedia.org/wiki/KISS_principle) principle (Keep it simple, stupid) to make the code more understandable, manageable, and maintainable.
- Roadmap/TODO
    - Graphical user interface
    - Logger

## Contribution Areas
We welcome contribution in the following areas:
- Minor incremental improvements: bug fixes or issues related to Spotify downloading functionality.
- Documentation updates or improvements to make the project easier to understand and use.
- Typo fixes in documentation.

We are currently not accepting:
- Changes that introduce features to download playlists from other services. (e.g. Apple Music, YouTube)
- Major rewrites or redesigns of the architecture. We prefer incremental improvements that keep the project minimalistic.

## License
By contributing to this project, you agree that your contributions will be licensed under the [LICENSE](LICENSE) file.