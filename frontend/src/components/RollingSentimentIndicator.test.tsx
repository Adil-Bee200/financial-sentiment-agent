import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { RollingSentimentIndicator } from './RollingSentimentIndicator'

describe('RollingSentimentIndicator', () => {
  it('renders rolling score and label', () => {
    render(<RollingSentimentIndicator rolling={0.18} />)

    expect(screen.getByText('7-day rolling')).toBeInTheDocument()
    expect(screen.getByText('+0.18')).toBeInTheDocument()
    expect(screen.getByText('Positive')).toBeInTheDocument()
  })

  it('shows placeholder when rolling is missing', () => {
    render(<RollingSentimentIndicator rolling={null} />)

    expect(screen.getByText('—')).toBeInTheDocument()
    expect(screen.getByText('Neutral')).toBeInTheDocument()
  })
})
