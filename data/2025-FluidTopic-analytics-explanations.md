# Fluid Topics Analytics numbers explanations

## Publication and topics

Fluid Topics handles content which are of different types:
https://doc.fluidtopics.com/r/Fluid-Topics-Configuration-and-Administration-Guide/Configure-a-Fluid-Topics-tenant/Knowledge-Hub/Types-of-content

- publication
  - article
  - book
- attachment
- unstructured document

A publication (book or article) contains a varying number of topics.
For the sake of the simulation you will define:
- `topic_size` the average size of a topic in characters
- `book_topic_number` the average number of topics per book
- `article_topic_number` the average number of topics per article
- `unstructured_document_size` the average size of an UD in characters

Attachment are neither translated nor subject to any generative AI treatment
so you can ignore them.

When a user uses Fluid Topics, the system defines a session during which he consults 
some content usually one or several topics (see above).

## Generative AI, Translation and profile

When using Generative AI or Machine Translation (MT) feature in Fluid Topics
the user uses an AI Profile 
(https://doc.fluidtopics.com/r/Fluid-Topics-Configuration-and-Administration-Guide/Configure-a-Fluid-Topics-tenant/AI)
which is typed depending of its usage:

- TRANSLATION for translation activities
- CHATBOT for conversational generative AI activities
- COMPLETION for simple (non conversational) generative AI activities

Each profile contains the provider and model used (e.g. OpenAI/gpt-5.1).
Completion and chatbot profile contains a prompt as well.

A completion profile usually act on a single topic whereas the chatbot profile
acts on several topics (ranging from 1 up to 50).

The data sent (input) to the LLM or MT is:
- the topic content for TRANSLATION profile, input_size=topic_size
- the topic content + the prompt COMPLETION profiles, input_size=topic_size+prompt_size
- the topics (1--50) contents + the prompt for CHABOT profile, input_size=n*topic_size+prompt_size

The data received (output) is:
- the translated topic content for TRANSLATION profile, output_size=topic_size
- the LLM generated output for COMPLETION profiles, output_size=200--400 characters
- the LLM generated output for CHABOT profile, output_size=200--400 characters

You can assume that `prompt_size` is the average size of a prompt in characters.

The given analytics gives you:
- a per day count of usage of profile usage.
- a per day count of session
- a per day count of book/article/etc... consulted

The session and book/article/etc... analytics are the one from
all Fluid Topic portal (N=213) but only part of (K=70) it has 
Generative AI and Translation feature activated, since this is an opt-in feature.

