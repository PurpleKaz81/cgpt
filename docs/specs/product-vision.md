# Product Vision

Last updated: 2026-02-16

## Purpose

Define what `cgpt` is, who it serves, and what it is intentionally not trying to solve in `v0.x`.

## Mission

`cgpt` helps a user turn prior AI conversations into reusable context summaries for better future AI conversations.

## Problem Statement

Users with long AI chat histories often cannot quickly recover the context they need for a new session. Manual rereading is slow, and chat UIs are not optimized for assembling cross-conversation context packets.

## Primary Users

- Individual users who keep substantial conversation history with AI assistants.
- Writers, researchers, and analysts who need continuity across sessions.
- Power users who want local CLI automation and repeatable workflows.

## Product Scope (Current)

- Process local export archives and conversation data.
- Support conversation discovery and selection from the local dataset.
- Generate dossier artifacts designed to be reused as context input for later AI chats.
- Prioritize reproducible CLI workflows over GUI-first features.

## Positioning and Tone

- Product description remains domain-neutral.
- Political, academic, business, and personal research use cases are all valid.
- Documentation should avoid niche framing in core product claims.

## Local-First Posture (`v0.x`)

- Default architecture is local-first and single-user.
- `config.personal.json` remains the recommended private local override pattern.
- Cloud-hosted workflows are considered future exploration, not current commitment.

## Current Hard Constraint

- Officially supported ingestion format is ChatGPT export ZIP content.
- Other provider formats are roadmap items and must not be represented as currently supported.

## Non-Goals (`v0.x`)

- Multi-tenant collaboration or shared cloud workspaces.
- Hosted account synchronization.
- Perfect autonomous finalization of a dossier without human or downstream AI refinement.
- GUI-first product parity with the CLI.

## Product Principles

- Privacy-aware by default: operate on local files and minimize unnecessary data movement.
- Reproducibility first: commands and outputs should be deterministic.
- Explicit status communication: docs must separate implemented behavior from planned direction.
- Small-scope delivery: ship incremental improvements by trimester.

## Beyond ChatGPT Direction

Long-term direction is provider-agnostic conversation context tooling. Priority sequence for expansion is:

1. Google (Gemini) compatibility path.
1. Perplexity compatibility path.
1. Broader provider abstraction and additional model ecosystems.
