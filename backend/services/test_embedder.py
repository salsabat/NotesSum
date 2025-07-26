from embedder import Embedder
from PineconeDB import PCDB

embedder = Embedder(PCDB(index_name='test-index'))

text = """The wind carried a scent of salt and distant rain, brushing gently against the sea grass that grew along the tops of the dunes. Elara stood there, barefoot, her toes sinking into the cool sand. It was early evening, the sky a gentle blend of lavender and soft rose, and the sun — now a glowing ember on the horizon — cast elongated shadows behind her. She had come here every summer since she was a child, but this visit felt different. Maybe it was the silence. Maybe it was the memories.

Behind her, the old cottage creaked in the wind, its whitewashed wood weathered from years of storms and sunshine. The shutters no longer closed properly, and the screen door had been torn for as long as she could remember. But it was home. Or at least, it had been. Now, it stood as a kind of monument — to her parents, to childhood, to all the things that no longer seemed permanent.

She walked slowly down the path toward the shore, her fingers brushing the tips of the wild grass. Each step stirred a memory. The time she’d raced her brother to the water, their laughter echoing in the stillness of dawn. The late-night fires with stories and songs, the smoke rising into a sky full of stars. Her father’s voice — calm, steady — telling her to watch the tide, to listen to the sea.

Now, the only sound was the surf.

The tide was low, revealing stretches of wet sand that gleamed like silver in the fading light. She knelt near the edge, drawing patterns in the sand with a piece of driftwood. Circles. Spirals. Lines that meant nothing, but helped her think. Or perhaps helped her not think.

She hadn’t planned to return this year. After her mother’s passing, everything had changed. The idea of coming back to the place where every corner held a memory had been almost unbearable. But something — maybe instinct, maybe longing — had pulled her here.

And now that she was here, she didn’t want to leave.

A gull cried overhead, circling once before diving toward the waves. Elara watched it with distant eyes, remembering how her mother used to call them messengers of change. “They always appear when something’s about to shift,” she used to say, wrapping an old shawl around her shoulders as they watched the birds dance in the wind.

Change. That’s all life seemed to be lately. One shift after another. One goodbye after the next.

The sun finally slipped below the edge of the world, leaving behind a soft glow. Night approached slowly, like a curtain being drawn across the sky. The first stars blinked awake, faint at first, but steady.

She turned back toward the dunes and climbed them again, this time more slowly. At the top, she paused and looked out across the land. The path she’d walked a thousand times looked unfamiliar in the twilight, as though it belonged to someone else. But the air was still warm with memory. It held her gently.

There was something sacred about returning to a place that had witnessed your growth. The dunes had seen her fall and rise, love and grieve, hope and despair. They’d held secrets and laughter. They were silent witnesses to everything she’d been — and everything she might still become.

She sat down cross-legged, letting the sand cool her legs. In the distance, the light from the old lighthouse blinked, its rhythm comforting. It no longer functioned as it once had, but the town kept it lit, more out of tradition than necessity. A symbol of guidance, even when no ships sailed nearby.

Elara stared at it, her thoughts drifting like clouds.

She remembered the stories her father used to tell her — about sailors who followed the light through storms, trusting it would lead them home. About the people who built it stone by stone, not for themselves, but for others who would never know their names. There was something noble in that. Something steady.

The lighthouse didn’t ask who you were. It just shone.

And maybe that’s what she needed. Not answers. Not closure. Just something steady. Something to remind her that even in darkness, there could be light.

She closed her eyes, the breeze brushing her cheeks like a whispered lullaby. And in that stillness, for the first time in a long time, she felt a sliver of peace. Not because everything was okay — but because it didn’t have to be. Because even here, even now, she could breathe.

And that was enough."""


# embed_document
embeddings = embedder.embed_document(text=text, category='text1')
print(len(embeddings))
print(embeddings[0])
print(len(embeddings[0]['values']))


# embed_query
result = embedder.embed_query('what is this')
print(result)
