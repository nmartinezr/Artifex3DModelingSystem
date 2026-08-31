# Image → 3D Style Presets

ARTIFEX treats artistic stylization and 3D reconstruction as separate concerns.

```text
Source image
  → image preprocessing
  → optional StylePreprocessor
  → styled conditioning image
  → selected ImageTo3DProvider
  → geometry validation
  → viewer / GLB / STL / 3MF
```

## Initial presets

- `none` — use the preprocessed source image unchanged.
- `collectible-vinyl` — oversized head, compact body, simplified facial features and sturdy printable forms.
- `chibi` — strongly exaggerated cute proportions.
- `anime-figure` — clean display-figure styling with simplified hair masses.
- `cartoon` — rounded, simplified character forms.
- `miniature` — small-scale readable details with reinforced thin features.
- `bobblehead` — oversized head with a compact body and sturdy neck connection.
- `realistic-bust` — portrait-oriented shoulders-and-head sculpture.
- `low-poly` — faceted stylized geometry with a strong silhouette.

The presets are intentionally brand-neutral. `collectible-vinyl` describes a general design language and does not depend on branded characters, logos or packaging.

## Real stylization runner

Set `ARTIFEX_STYLE_COMMAND` to an external image-generation or image-editing runner. ARTIFEX invokes it as:

```text
<command> --request <request.json>
```

The request contains the source image path, selected style ID, positive/negative prompts and an output directory. The runner must write `result.json`:

```json
{
  "image": {
    "path": "styled.png",
    "mediaType": "image/png"
  }
}
```

The model used behind this runner remains replaceable. This allows ARTIFEX to benchmark identity-preserving image-editing models independently from TRELLIS, SPAR3D, Stable Fast 3D or any future 3D provider.

## Failure behavior

Selecting `style=none` requires no style runner. Selecting any stylized preset without `ARTIFEX_STYLE_COMMAND` configured returns `IMAGE_TO_3D_STYLE_UNAVAILABLE`; ARTIFEX never claims a style was applied when it was not.
