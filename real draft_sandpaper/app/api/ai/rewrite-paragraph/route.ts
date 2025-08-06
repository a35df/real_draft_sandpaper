import { NextResponse } from 'next/server';
import { geminiModel } from '@/lib/gemini';
import { Paragraph, ReferenceCard } from '@/types';

export async function POST(request: Request) {
  try {
    const { targetParagraph, referenceCard }: { targetParagraph: Paragraph; referenceCard: ReferenceCard } = await request.json();

    const prompt = `
      As a writing assistant for a webnovel author, rewrite the following paragraph to be more vivid and engaging, using the information from the provided reference card.
      Do not change the core meaning, but enhance the description, dialogue, or pacing.
      Respond with only the rewritten paragraph text, without any extra explanations or markdown.

      Original Paragraph:
      "${targetParagraph.content}"

      ---

      Reference Card to Apply:
      - Title: ${referenceCard.title}
      - Summary: ${referenceCard.summary}

      ---

      Rewritten Paragraph:
    `;

    const result = await geminiModel.generateContent(prompt);
    const rewrittenText = await result.response.text();

    return NextResponse.json({ rewrittenText });

  } catch (error) {
    console.error('Error rewriting paragraph:', error);
    return NextResponse.json({ error: 'Failed to rewrite paragraph' }, { status: 500 });
  }
}
