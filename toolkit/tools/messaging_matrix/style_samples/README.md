# Style Samples

This folder holds writing samples and reference materials used to generate personalized style guides for the Messaging Matrix tool.

## Structure

Each document type has two subfolders:

```
<document_type>/
  my_samples/    -- Your own writing (the tool learns your personal voice)
  references/    -- Best practice guides, how-to docs, style manuals, examples
```

### Document types

| Folder | What goes in `my_samples/` | What goes in `references/` |
|--------|---------------------------|---------------------------|
| `social_media/` | Your social media posts | Social media writing guides |
| `press_releases/` | Your press releases / news releases | PR writing best practices |
| `talking_points/` | Your Hill talking points | TP format guides, examples |
| `op_eds/` | Your op-eds, opinion pieces | Op-ed writing guides |
| `speeches/` | Your speech drafts | Speechwriting guides |
| `media_talking_points/` | Your media/spokesperson TPs | Media training materials |

## Supported file formats

- PDF (.pdf)
- Word documents (.docx)
- Plain text (.txt)

## How to use

1. Drop your files into the appropriate `my_samples/` and/or `references/` subfolders
2. Open the Messaging Matrix page in the Streamlit app
3. Expand the "Writing Style" section at the bottom
4. Click "Build Style Guide" — the tool will analyze all samples and generate style guides
5. Style guides are saved in `style_guides/` and automatically applied to future generations

## Notes

- You only need to rebuild style guides when you add new samples
- The more samples you provide, the better the style matching
- Having both `my_samples/` and `references/` produces the best results (personal voice + professional standards)
- Generated style guides are editable — feel free to refine them manually
- This folder is gitignored (except this README) to protect personal/client work
