import { describe, expect, it } from 'vitest'
import {
  formatScore,
  getSentimentColor,
  getSentimentLabel,
  scoreToGaugePosition,
} from './sentiment'

describe('sentiment helpers', () => {
  it('maps scores to labels', () => {
    expect(getSentimentLabel(0.6)).toBe('Strong Positive')
    expect(getSentimentLabel(0.2)).toBe('Positive')
    expect(getSentimentLabel(0)).toBe('Neutral')
    expect(getSentimentLabel(-0.3)).toBe('Negative')
    expect(getSentimentLabel(null)).toBe('Neutral')
  })

  it('formats signed scores', () => {
    expect(formatScore(0.291)).toBe('+0.29')
    expect(formatScore(-0.12)).toBe('-0.12')
    expect(formatScore(null)).toBe('—')
  })

  it('maps gauge position from -1..1 to 0..1', () => {
    expect(scoreToGaugePosition(-1)).toBe(0)
    expect(scoreToGaugePosition(0)).toBe(0.5)
    expect(scoreToGaugePosition(1)).toBe(1)
  })

  it('assigns color classes by score band', () => {
    expect(getSentimentColor(0.5)).toContain('emerald')
    expect(getSentimentColor(0)).toContain('amber')
    expect(getSentimentColor(-0.5)).toContain('red')
  })
})
