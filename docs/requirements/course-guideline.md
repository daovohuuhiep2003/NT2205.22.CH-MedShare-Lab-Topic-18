**COURSE PROJECT GUIDELINE**
**Cryptography and Applications**
_For Undergraduate and Graduate Students_

| **Core project philosophy**                                                                                                                                                                                                                                       |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Do not start from a cryptographic algorithm. Start from the system, assets, threats, and security requirements; then derive cryptographic requirements, select mechanisms, implement them securely, test them adversarially, and evaluate the resulting evidence. |

**System Analysis  →  Assets  →  Threat Model  →  Security Requirements  
→  Security Architecture  →  Cryptographic Requirements  →  Cryptographic Mechanisms  
→  Implementation  →  Security Testing  →  Evaluation**

Use this document before reading the detailed project topics. Every assigned topic must be developed through the same lifecycle.
# 1. Purpose and expected mindset

This guideline defines the common engineering and academic logic for all course projects in Cryptography and Applications. The detailed project topic determines the application domain; this document determines how the project must be reasoned about, designed, implemented, tested, and evaluated.
·        Begin with a security problem in a concrete system, not with an algorithm name.
·        Separate security requirements from cryptographic requirements.
·        Treat cryptographic keys, trust anchors, certificates, nonces, and protocol state as security-critical assets.
·        Justify every cryptographic mechanism by a requirement and an attacker capability.
·        Provide evidence through testing and evaluation; successful execution alone is not evidence of security.
·        Keep a traceable chain from threat to requirement, mechanism, implementation, test, and result.

| **Central reasoning rule**                                                                                                                                |
| --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Threat → Security Property → Cryptographic Property → Mechanism → Implementation → Test → Evidence. A direct “Threat → Algorithm” jump is not acceptable. |
# 2. Common lifecycle for every project

|**#**|**Phase**|**Primary question**|
|---|---|---|
|**1**|**System & Trust Analysis**|Define system boundary, entities, data flows, trust boundaries, and attacker-controlled surfaces.|
|**2**|**Asset Identification**|Identify what must be protected and why its compromise matters.|
|**3**|**Threat & Attacker Model**|State attacker capabilities, knowledge, access, and realistic attack scenarios.|
|**4**|**Security Requirements**|Translate threats into explicit system-level security properties.|
|**5**|**Security Architecture**|Place trust, authentication, key management, secure channels, and protection boundaries in the architecture.|
|**6**|**Cryptographic Requirements**|Convert system-level properties into precise cryptographic properties and constraints.|
|**7**|**Cryptographic Design & Mechanisms**|Select primitives, protocols, parameters, and key-management mechanisms that satisfy the requirements.|
|**8**|**Secure Implementation**|Implement with correct APIs, key lifecycle, randomness, nonce handling, validation, and failure behavior.|
|**9**|**Security & Adversarial Testing**|Test normal operation and actively test misuse, tampering, replay, forgery, invalid state, and other attacker actions.|
|**10**|**Evaluation & Evidence**|Evaluate whether the original requirements are satisfied and identify residual risks and trade-offs.|
The lifecycle is iterative, not merely sequential. A failed test may require revisiting the cryptographic design, architecture, threat model, or even the initial system assumptions.
# 3. Phase-by-phase project guidance
## Phase 1. System & Trust Analysis
_Establish exactly what system is being protected before discussing cryptography._
## Guiding questions
·        What are the actors, components, interfaces, data stores, and external services?
·        What data flows exist, and over which channels?
·        Where are the trust boundaries?
·        Which components or channels can the attacker observe, modify, control, or compromise?
·        What assumptions are made about endpoints, operating systems, cloud services, hardware, or administrators?
## Minimum deliverables
·        System architecture diagram.
·        Data-flow diagram.
·        Trust-boundary annotation.
·        Short list of system assumptions and out-of-scope conditions.

| **Undergraduate expectation**                                                                                         | **Graduate expectation**                                                                                                  |
| --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Provide a clear architecture and data-flow view with explicit trust boundaries and realistic assumptions.             | Provide a more formal trust model, justify assumptions, and discuss how changing assumptions affects the security design. |
| **Key checkpoint**<br>A project that cannot clearly state its trust boundary cannot make a defensible security claim. |                                                                                                                           |
## Phase 2. Asset Identification
_Identify the information, identities, keys, state, and services whose compromise would cause security impact._
## Guiding questions
·        Which data require confidentiality, integrity, authenticity, availability, or privacy?
·        Which identities and credentials are security-critical?
·        Which cryptographic keys, trust anchors, certificates, nonces, counters, or protocol states are assets?
·        What is the consequence of disclosure, modification, destruction, duplication, or misuse of each asset?
## Minimum deliverables
·        Asset table with owner, location, value, and required protection.
·        Key and credential inventory.
·        Prioritization of high-value assets.

| **Undergraduate expectation**                                                                                       | **Graduate expectation**                                                        |
| ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Identify and classify all main assets and explain their required protection.                                        | Add dependency analysis between assets and identify cascading compromise paths. |
| **Key checkpoint**<br>Cryptographic keys must be treated as first-class assets, not merely as algorithm parameters. |                                                                                 |
## Phase 3. Threat & Attacker Model
_Define the attacker before defining the cryptographic defense._
## Guiding questions
·        Can the attacker eavesdrop, modify, inject, replay, reorder, or block messages?
·        Can the attacker impersonate users, servers, devices, or services?
·        Can the attacker obtain ciphertext, known plaintext, chosen inputs, public keys, leaked credentials, or compromised storage?
·        Can the attacker exploit protocol downgrade, key substitution, weak randomness, nonce reuse, or implementation errors?
·        For graduate work: is a classical attacker sufficient, or must quantum capabilities and store-now-decrypt-later risk be considered?
## Minimum deliverables
·        Attacker-capability table.
·        Threat scenarios linked to assets and system components.
·        Threat-priority/risk rationale.

| **Undergraduate expectation**                                                                            | **Graduate expectation**                                                                                                                       |
| -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Use a clear threat model and several concrete attack scenarios.                                          | State attacker knowledge/capabilities more explicitly; compare alternative threat models and, where relevant, classical vs. quantum attackers. |
| **Key checkpoint**<br>Do not claim protection against an attacker whose capabilities were never defined. |                                                                                                                                                |
## Phase 4. Security Requirements
_Translate threats into system-level security properties before choosing algorithms._
## Guiding questions
·        Which threats require confidentiality, integrity, authentication, freshness, non-replay, non-repudiation, forward secrecy, key compromise containment, or other properties?
·        Which requirements apply to data in transit, data at rest, identity, software, logs, or session state?
·        Which requirements are mandatory, and which are desirable?
·        How will each requirement later be verified?
## Minimum deliverables
·        Numbered security requirements (SR-01, SR-02, …).
·        Threat-to-requirement mapping.
·        Verification criterion for each requirement.

| **Undergraduate expectation**                                                                                                                                  | **Graduate expectation**                                                                                                |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Write explicit and testable security requirements.                                                                                                             | Express stronger security goals, dependencies, assumptions, and verification criteria; avoid vague CIA-only statements. |
| **Key checkpoint**<br><br>“Need confidentiality” is too vague unless the protected asset, attacker capability, context, and verification criterion are stated. |                                                                                                                         |
## Phase 5. Security Architecture
_Decide where trust and security controls belong before selecting cryptographic primitives._
## Guiding questions
·        How are identities established and authenticated?
·        Where are trust anchors, certificates, public keys, or shared secrets obtained?
·        Where are sessions established and terminated?
·        Which communication paths require secure channels?
·        Where are keys generated, stored, rotated, revoked, and destroyed?
·        What happens if one component is compromised?
## Minimum deliverables
·        Security architecture diagram.
·        Authentication and trust model.
·        Key-management architecture.
·        Security boundaries and control placement.

| **Undergraduate expectation**                                                                                      | **Graduate expectation**                                                                                          |
| ------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| Show how identity, secure channels, storage protection, and key management fit into the system.                    | Analyze architectural alternatives and compromise containment; justify trust-anchor and key-management decisions. |
| **Key checkpoint**<br><br>Cryptography is a component of security architecture; it is not the architecture itself. |                                                                                                                   |
## Phase 6. Cryptographic Requirements
_Convert system security requirements into the precise properties expected from cryptographic components._
## Guiding questions
·        Does confidentiality require passive secrecy only, or protection against active/chosen-ciphertext attacks?
·        Is integrity required for messages, ciphertexts, software artifacts, public keys, or logs?
·        Is entity authentication, message authentication, or both required?
·        Are freshness, key separation, forward secrecy, post-compromise security, or long-term quantum resistance required?
·        What security level, key lifetime, performance, interoperability, and deployment constraints apply?
## Minimum deliverables
·        Cryptographic requirement list (CR-01, CR-02, …).
·        Mapping SR → CR.
·        Security level and operational constraints.

| **Undergraduate expectation**                                                                                                                      | **Graduate expectation**                                                                                                                                                             |
| -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| State the required cryptographic function and practical constraints clearly.                                                                       | Where appropriate, connect requirements to formal notions (e.g., AEAD integrity/confidentiality, unforgeability, authenticated key exchange, forward secrecy) and state assumptions. |
| **Key checkpoint**<br><br>The question at this stage is “What property must the cryptography guarantee?”, not “Which algorithm do we want to use?” |                                                                                                                                                                                      |
## Phase 7. Cryptographic Design & Mechanisms
_Select primitives, protocols, parameters, and compositions only after requirements are clear._
## Guiding questions
·        Which primitive or protocol family satisfies each cryptographic requirement?
·        Are authenticated encryption, KDFs, MACs, digital signatures, KEM/key agreement, password hashing, certificates, or hybrid constructions needed?
·        Are the selected parameters and security levels appropriate?
·        How are multiple primitives composed, and is key separation enforced?
·        What alternatives exist, and why is the selected design preferable in this deployment?
## Minimum deliverables
·        Cryptographic design diagram.
·        Mechanism/parameter table.
·        Key hierarchy and key-derivation plan.
·        Design rationale and alternatives considered.

| **Undergraduate expectation**                                                                                                                          | **Graduate expectation**                                                                                                             |
| ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| Use modern, standard mechanisms correctly and justify the main choices.                                                                                | Compare alternatives, assumptions, security notions, performance, crypto-agility, and—where relevant—post-quantum or hybrid designs. |
| **Key checkpoint**<br><br>Algorithm popularity is not a sufficient design justification. The mechanism must trace back to a cryptographic requirement. |                                                                                                                                      |

## Phase 8. Secure Implementation
_Translate the cryptographic design into code without invalidating its security assumptions._
## Guiding questions
·        Are approved cryptographic libraries and high-level APIs used correctly?
·        How are randomness, IVs/nonces, salts, counters, tags, and associated data generated and validated?
·        Are keys hard-coded, logged, serialized insecurely, or kept in memory longer than necessary?
·        Are certificates, public keys, signatures, tags, and error conditions validated correctly?
·        Are protocol states and failure paths safe?
·        Is sensitive data exposed through logs, exceptions, temporary files, or debug interfaces?
## Minimum deliverables
·        Working implementation.
·        Configuration/parameter file.
·        Key lifecycle description.
·        Security-critical code walkthrough.
·        Reproducible build/run instructions.

| **Undergraduate expectation**                                                                                                                                     | **Graduate expectation**                                                                                                                                  |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Demonstrate correct cryptographic API use and safe key/nonce handling.                                                                                            | Additionally analyze misuse resistance, failure behavior, side-channel exposure where relevant, dependency choices, and implementation/architecture gaps. |
| **Key checkpoint**<br><br>A mathematically secure primitive can become insecure through incorrect nonce use, validation, key storage, composition, or API misuse. |                                                                                                                                                           |
## Phase 9. Security & Adversarial Testing
_Test the security claims by deliberately violating assumptions, modifying data, and simulating attacker actions._
## Guiding questions
·        Does normal encryption/decryption or signing/verification work correctly?
·        What happens when ciphertext, tag, signature, key, certificate, nonce, counter, or associated data is modified?
·        Are replayed, reordered, duplicated, downgraded, or forged messages rejected?
·        Can a public key be substituted or an endpoint impersonated?
·        What happens under wrong keys, expired credentials, corrupted state, partial data, or malformed input?
·        Are negative tests automated and reproducible?
## Minimum deliverables
·        Functional test set.
·        Cryptographic negative tests.
·        Adversarial test scenarios.
·        Test logs/evidence.
·        Expected vs. observed results.

| **Undergraduate expectation**                                                     | **Graduate expectation**                                                                                                                                 |
| --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Include both positive and negative tests, with several attacker-driven scenarios. | Design adversarial experiments that connect explicitly to the threat model; discuss coverage, limitations, and false confidence from incomplete testing. |
| **Key checkpoint**<br><br>“The program runs successfully” is not a security test. |                                                                                                                                                          |
## Phase 10. Evaluation & Security Evidence
_Return to the original requirements and determine what is actually supported by evidence._
## Guiding questions
·        Which security requirements were verified, partially verified, or not verified?
·        Which tests provide evidence for each requirement?
·        What assumptions remain untested?
·        What residual risks remain after the cryptographic controls are deployed?
·        What trade-offs exist among security, performance, complexity, compatibility, and maintainability?
·        What would need to change for a stronger attacker or a different deployment environment?
## Minimum deliverables
·        Requirement–mechanism–test–evidence matrix.
·        Performance/resource measurements where relevant.
·        Residual-risk discussion.
·        Limitations and future improvements.
·        Final security claim scoped to the stated threat model.

| **Undergraduate expectation**                                                                                                                                                      | **Graduate expectation**                                                                                                                                          |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Evaluate requirement coverage and explain limitations honestly.                                                                                                                    | Provide a stronger evidence-based argument, including assumptions, residual risks, security/performance trade-offs, and sensitivity to alternative threat models. |
| **Key checkpoint**<br><br>A valid conclusion is scoped: “Under assumptions A and threat model T, tests E support requirements R.” Avoid claiming that a system is simply “secure.” |                                                                                                                                                                   |
# 4. Required traceability matrix
Every project must maintain a traceability matrix. The matrix may be expanded as the project develops, but the logical chain must remain visible.

|**Threat / Attack**|**Security Requirement**|**Cryptographic Requirement**|**Mechanism**|**Implementation Control**|**Security Test**|**Evidence / Result**|
|---|---|---|---|---|---|---|
|Eavesdropping|Confidentiality of session data|Authenticated confidentiality under the stated active-network threat model|AEAD|Unique nonce; key separation; correct AAD|Capture traffic; modify ciphertext/tag|Plaintext not exposed; modified record rejected|
|Replay|Freshness / non-replay|Replay-resistant session/message processing|Counter/nonce + authenticated state|Track accepted sequence/state|Replay previously valid record|Replay rejected|
|Impersonation|Endpoint authentication|Authenticated key establishment or signature verification|Certificate/signature or authenticated KEX|Validate identity binding / trust anchor|Key substitution / forged identity attempt|Untrusted identity rejected|
The examples above illustrate the form only. Students must build a matrix specific to the assigned system and threat model.
# 5. Minimum project artifacts

|**ID**|**Artifact**|**Minimum content**|
|---|---|---|
|**A1**|**System model**|Architecture, data flow, trust boundaries, assumptions.|
|**A2**|**Asset inventory**|Data, identities, credentials, keys, state, services, impact.|
|**A3**|**Threat model**|Attacker capabilities and prioritized attack scenarios.|
|**A4**|**Security requirements**|Numbered, testable system-level requirements.|
|**A5**|**Security architecture**|Trust, authentication, key management, secure-channel placement.|
|**A6**|**Cryptographic requirements**|Properties, security levels, operational constraints.|
|**A7**|**Cryptographic design**|Mechanisms, parameters, key hierarchy, alternatives and rationale.|
|**A8**|**Implementation**|Source code, configuration, reproducible run instructions.|
|**A9**|**Security tests**|Positive, negative, and adversarial tests with evidence.|
|**A10**|**Evaluation**|Traceability matrix, results, residual risks, limitations, conclusion.|
# 6. Recommended final report structure
1.      Problem statement and project scope
2.      System and trust analysis
3.      Asset identification
4.      Threat and attacker model
5.      Security requirements
6.      Security architecture
7.      Cryptographic requirements
8.      Cryptographic design and mechanism selection
9.      Implementation
10.   Security and adversarial testing
11.   Evaluation, evidence, residual risks, and limitations
12.   Conclusion
13.   Appendices: source-code structure, test cases, configuration, detailed logs/results as needed.

| **Important**                                                                                                                                                    |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| The report should explain the reasoning chain. Avoid turning Sections 7–8 into a catalogue of algorithms or a general textbook summary unrelated to the project. |
# 7. Undergraduate vs. Graduate depth

| **Dimension**  | **Undergraduate**                                         | **Graduate**                                                                                            |
| -------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| System model   | Clear architecture, flows, trust boundaries.              | More formal trust model; analyze changing assumptions.                                                  |
| Threat model   | Concrete attacker capabilities and scenarios.             | Alternative attacker models; stronger capability analysis; quantum threat when relevant.                |
| Requirements   | Explicit, testable security requirements.                 | Stronger security properties, assumptions, and formal notions where appropriate.                        |
| Crypto design  | Correct use of modern standard mechanisms.                | Compare constructions, assumptions, security notions, crypto-agility, and trade-offs.                   |
| Implementation | Correct APIs, randomness, nonce/key handling, validation. | Analyze misuse resistance, side channels where relevant, failure modes, dependency/security boundaries. |
| Testing        | Positive, negative, and adversarial scenarios.            | Threat-model-driven experiments; coverage and limitations; deeper attack analysis.                      |
| Evaluation     | Requirement coverage and limitations.                     | Evidence-based security argument with residual risk and security/performance/assumption trade-offs.     |
# 8. Suggested evaluation rubric
The lecturer may adjust weights for a specific topic, but grading should reward security reasoning and evidence rather than code volume alone.

|**Criterion**|**Weight**|**Evidence expected**|
|---|---|---|
|**System, assets, threat model**|**15%**|Correct scope, realistic trust assumptions, prioritized threats.|
|**Security requirements & architecture**|**15%**|Traceable requirements and defensible control placement.|
|**Cryptographic requirements & design**|**20%**|Correct properties, mechanism selection, parameters, composition, rationale.|
|**Secure implementation**|**20%**|Correct APIs, key lifecycle, randomness/nonce handling, validation, robust failure behavior.|
|**Security/adversarial testing**|**15%**|Meaningful negative/adversarial tests tied to attacker capabilities.|
|**Evaluation & evidence**|**10%**|Traceability, residual risks, limitations, security/performance trade-offs.|
|**Report/demo quality**|**5%**|Reproducibility, clarity, technical communication.|
# 9. Common project failures to avoid
·        Starting with “we use AES/RSA/ECC/ML-KEM…” before defining the security problem.
·        Listing CIA properties without linking them to concrete assets and threats.
·        Using encryption without authenticity/integrity where the attacker can modify data.
·        Ignoring identity, trust anchors, public-key binding, certificates, or key distribution.
·        Hard-coding keys or reusing nonces/IVs.
·        Writing custom cryptographic primitives when the project does not explicitly require cryptographic research.
·        Treating successful encryption/decryption as sufficient security testing.
·        Testing only valid inputs and normal workflows.
·        Claiming “the system is secure” without defining the attacker and assumptions.
·        Reporting benchmark numbers without interpreting their security or deployment implications.
# 10. Pre-submission checklist
□ The system boundary and trust boundary are explicit.
□ Assets include keys, credentials, identities, and protocol state where relevant.
□ Attacker capabilities are stated.
□ Every major threat maps to at least one security requirement.
□ Every cryptographic mechanism maps to a cryptographic requirement.
□ Algorithm parameters, keys, nonces, salts, randomness, and lifetimes are documented.
□ Key generation, storage, rotation/revocation/destruction are addressed where relevant.
□ Security-critical API use and validation behavior are explained.
□ Negative and adversarial tests are included.
□ The traceability matrix contains evidence/results.
□ Residual risks and limitations are stated.
□ The conclusion is scoped to the defined threat model and assumptions.

| **Final principle**                                                                                                                                                                                                                                |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| The strongest course project is not the one that uses the largest number of cryptographic algorithms. It is the one that shows the clearest and best-supported chain from system security problem to cryptographic design and verifiable evidence. |
