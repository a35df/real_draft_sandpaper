import { NextResponse } from 'next/server';
import { geminiModel } from '@/lib/gemini';
import { Episode, Paragraph, ReferenceCard } from '@/types';

// POST 요청을 처리하는 함수
export async function POST(request: Request) {
  try {
    const { episodeContext, targetParagraph }: { episodeContext: Episode; targetParagraph: Paragraph } = await request.json();

    // Gemini API에 전달할 프롬프트 생성
    const prompt = `
      As a writing assistant for a webnovel author, generate 6 reference cards based on the following episode context and the specific paragraph the author is working on.
      Each card should provide a specific, actionable piece of information (e.g., a sensory detail, a historical fact, a character motivation, a dialogue suggestion).
      The title should be a concise keyword (1-3 words), and the summary should be a short, helpful description (1-2 sentences).

      Episode Title: ${episodeContext.title}
      Full Episode Content:
      ${episodeContext.paragraphs.map(p => p.content).join('\n')}

      ---

      Author's Target Paragraph:
      "${targetParagraph.content}"

      ---

      Generate the 6 cards in a valid JSON array format like this:
      [
        {"title": "Card Title 1", "summary": "Card summary 1."},
        {"title": "Card Title 2", "summary": "Card summary 2."},
        ...
      ]
    `;

    const result = await geminiModel.generateContent(prompt);
    const responseText = await result.response.text();

    // Gemini 응답에서 JSON 부분만 추출
    const jsonResponse = responseText.match(/\[[\s\S]*\]/);
    if (!jsonResponse) {
      throw new Error('Invalid JSON response from AI');
    }

    const cards: Omit<ReferenceCard, 'id' | 'isPinned' | 'group' | 'isInHold'>[] = JSON.parse(jsonResponse[0]);

    // 클라이언트에 생성된 카드 목록을 반환
    return NextResponse.json(cards);

  } catch (error) {
    console.error('Error generating reference cards:', error);
    return NextResponse.json({ error: 'Failed to generate cards' }, { status: 500 });
  }
}
