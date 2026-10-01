---
title: "StructMoE: Structured Mixture of Experts Using Low Rank Experts"
date: 2024-01-01
authors: ["Zain Sarwar", "Ashwinee Panda", "Benjamin Thérien", "Stephen Rawls", "Anirban Das", "Kartik Balasubramaniam", "Berkcan Kapusuzoglu", "Shixiong Zhang", "Sambit Sahu", "Milind Naphade", "Supriyo Chakraborty"]
venue:
  name: "NeurIPS Efficient Natural Language and Speech Processing Workshop"
  type: workshop
status: published
links:
  - label: "Read publisher paper"
    url: "https://proceedings.mlr.press/v262/sarwar24a.html"
topics: ["engineering", "machine learning"]
featured: false
summary: "We introduce StructMoE, a method to scale MoE architectures by augmenting experts with dynamic capacity using structured matrices we call Low Rank Experts (LoRE). These LoREs are selected on a per-expert and per-token basis using a secondary router specific to every expert and are entangled with the main expert in the up-projection phase of the expert before the activation function. Empirically, we find this approach to outperform an MoE baseline in terms of loss on a held out validation set."
contribution: "We introduce StructMoE, a method to scale MoE architectures by augmenting experts with dynamic capacity using structured matrices we call Low Rank Experts (LoRE). These LoREs are selected on a per-expert and per-token basis using a secondary router specific to every expert and are entangled with the main expert in the up-projection phase of the expert before the activation function. Empirically, we find this approach to outperform an MoE baseline in terms of loss on a held out validation set."
---
