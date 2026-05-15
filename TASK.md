# Take-Home Assignment: Fintech Risk Monitoring

# System

## Overview

Design and implement a simplified fintech risk monitoring system. The goal is to evaluate your
ability to make technical decisions, design architecture, and ship a working solution.

## Core Requirement

Backend must be implemented using FastAPI. All other technology choices are up to you.

## Functional Tasks (Must Be Implemented via API Routes)

- Create a business (POST /businesses)
- Get list of businesses with basic filtering (GET /businesses)
- Get detailed business info including risk data (GET /businesses/{id})
- Run or trigger risk evaluation for a business (POST /businesses/{id}/evaluate)
- Return history of risk evaluations for a business (GET /businesses/{id}/risk-history)

## Behavior Expectations

- Risk evaluation can be simulated (e.g., random score or simple logic)
- System should store historical risk results
- API should handle errors and invalid input gracefully

## Technical Expectations

- Design clean FastAPI architecture
- Use a database of your choice
- Provide a UI (any framework)
- Containerize the system (e.g., Docker)
- Project should run locally with clear setup instructions

## Important Note

You are allowed to use AI tools (ChatGPT, Claude, etc.) during this assignment. What matters is
your ability to make decisions, structure the system, and explain your choices.


## Deliverables

- GitHub repository
- README with setup instructions
- Short explanation of architecture and decisions
