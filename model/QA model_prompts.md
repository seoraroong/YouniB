## 실험 내용
- Few shot 개수(1,2,4)
- 프롬프트 구조 (Context + Instruct, Instruct + Context)

### QA model Context + Instruct
```
M_context_prompt_format = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert in generating quizzes.
Given the context regarding biology, create a single multiple-choice question that accurately tests knowledge based on the context.

Context: {0}

If you decide to provide a quiz, you MUST strictly follow the format below:
The format for the multiple-choice quiz is:

  Question: <Your Question Here>
  Options:
  <Option A>
  <Option B>
  <Option C>
  <Option D>
  Answer: <Correct Option>

Additional rules:
1. Include exactly four options in the \"Options\" list.
2. Avoid repeating any information across the options.
3. Ensure that one and only one option is correct.
4. Ensure that the question and options are directly related to the provided context.
5. You SHOULD NOT include any other text in the response.
<|eot_id|><|start_header_id|>user<|end_header_id|>

Now create a single multiple-choice question.
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

S_context_prompt_format = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert in generating quizzes.
Given the context regarding biology, create a single short-answer question that accurately tests knowledge based on the context.

Context: {0}

If you decide to provide a quiz, you MUST strictly follow the format below:

Question: <Your Question Here>
Answer: <Correct Answer>

Additional rules:
1. Ensure the question and answer are directly related to the provided context.
2. Include only one correct answer.
3. You SHOULD NOT include any other text in the response.
<|eot_id|><|start_header_id|>user<|end_header_id|>

Now create a single short-answer question.
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

```


### QA model FS 2
```
M_context_prompt_format = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert in generating quizzes.
Given the context regarding biology, create a single multiple-choice question that accurately tests knowledge based on the context.
If you decide to provide a quiz, you MUST strictly follow the format below:
The format for the multiple-choice quiz is:

  Question: <Your Question Here>
  Options:
  <Option A>
  <Option B>
  <Option C>
  <Option D>
  Answer: <Correct Option>

Additional rules:
1. Include exactly four options in the \"Options\" list.
2. Avoid repeating any information across the options.
3. Ensure that one and only one option is correct.
4. Ensure that the question and options are directly related to the provided context.
5. You SHOULD NOT include any other text in the response.
<|eot_id|><|start_header_id|>user<|end_header_id|>

The following are two example of multiple-choice question-and-answer using the few-shot technique.

Context :  Protein structure Peptide bonds and polypeptides The Cast of ChemicalsProtein structure Four levels of protein structure Primary Secondary Tertiary Quaternary The Cast of Chemicals Channel proteins (ion channels) Polar R groups and nonpolar R groups Ion selectivity: Diameter of the pore and the nature of R group lining Gating: Selectively open and close the ion transport by conformational changes Membrane ion channel Ion pumps Formed by membrane-spanning proteins Use energy from ATP breakdown to transport ions Neuronal signalling: Sodium and Calcium The Movement of Ions The existence of a bridge cross An open channel protein does not mean that there is a movement of ions Ionic movements are influenced by two factors Diffusion Electricity

  Question: What is the primary energy source used by ion pumps to transport ions across the membrane?
  Options:
  A. Glucose
  B. ATP breakdown
  C. Diffusion gradients
  D. Oxygen
  Answer: B

Context : Taste bud Gustatory axon Brain stem Thalamus Cerebral cortex Three cranial nerves carry taste information into the brain Facial nerve (Cranial nerve VII) anterior 2/3 Glossopharyneal nerve (Cranial nerve IX) posterior 1/3 Vagus nerve (Cranial nerve X) throat (glottis, epiglottis, pharynx)  Gustatory nucleus the brain stem : where the afferent nerves innervates  Gustatory nucleus Cerebral cortex Gustatory nucleus thalamus Ventral posterior medial (VPM) nucleus Primary gustatory cortex Lesions within VPM or Primary gustatory cortex leads to Ageusia (the loss of taste perception) Gustation Important to the control of feeding and digestion Gustatory nucleus cells project to Medulla : swallowing, salivation, gagging, vomitting Hypothalamus and Basal telencephalon : palatability, motivate to eat Lesions in the hypothalamus/amygdala, basal telencephalon : overeat or ignore food, alter preference for food types The Neural Coding of Taste Labeled line hypothesis Individual taste receptor cells for each stimuli In reality, most neurons are broadly tuned (they are less specific) Gustatory nucleus receive synapses from many axons of different taste axons Population coding Roughly labeled lines Large numbers of broadly tuned neurons Contribution of temperature and textural features of food Warns of harmful substances, combines with taste for identifying foods Pheromones a mode of communication Reproductive behavior Territorial boundaries Identification of individuals Signal aggression or submission Role of human pheromones unclear

  Question: Which cranial nerve is responsible for carrying taste information from the throat, including the glottis and epiglottis?
  Options:
  A. Facial nerve (Cranial nerve VII)
  B. Glossopharyngeal nerve (Cranial nerve IX)
  C. Vagus nerve (Cranial nerve X)
  D. Hypoglossal nerve (Cranial nerve XII)
  Answer: C

Context: {0}
Now create a single multiple-choice question.
<|eot_id|>

<|start_header_id|>assistant<|end_header_id|>
"""

S_context_prompt_format = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert in generating quizzes.
Given the context regarding biology, create a single short-answer question that accurately tests knowledge based on the context.
If you decide to provide a quiz, you MUST strictly follow the format below:

Question: <Your Question Here>
Answer: <Correct Answer>

Additional rules:
1. Ensure the question and answer are directly related to the provided context.
2. Include only one correct answer.
3. You SHOULD NOT include any other text in the response.
<|eot_id|><|start_header_id|>user<|end_header_id|>

The following are two example of a short-answer question-and-answer using the few-shot technique.

Context :  Protein structure Peptide bonds and polypeptides The Cast of ChemicalsProtein structure Four levels of protein structure Primary Secondary Tertiary Quaternary The Cast of Chemicals Channel proteins (ion channels) Polar R groups and nonpolar R groups Ion selectivity: Diameter of the pore and the nature of R group lining Gating: Selectively open and close the ion transport by conformational changes Membrane ion channel Ion pumps Formed by membrane-spanning proteins Use energy from ATP breakdown to transport ions Neuronal signalling: Sodium and Calcium The Movement of Ions The existence of a bridge cross An open channel protein does not mean that there is a movement of ions Ionic movements are influenced by two factors Diffusion Electricity
  Question: What is the energy source used by ion pumps to transport ions across membranes?
  Answer: ATP breakdown

Context : Taste bud Gustatory axon Brain stem Thalamus Cerebral cortex Three cranial nerves carry taste information into the brain Facial nerve (Cranial nerve VII) anterior 2/3 Glossopharyneal nerve (Cranial nerve IX) posterior 1/3 Vagus nerve (Cranial nerve X) throat (glottis, epiglottis, pharynx)  Gustatory nucleus the brain stem : where the afferent nerves innervates  Gustatory nucleus Cerebral cortex Gustatory nucleus thalamus Ventral posterior medial (VPM) nucleus Primary gustatory cortex Lesions within VPM or Primary gustatory cortex leads to Ageusia (the loss of taste perception) Gustation Important to the control of feeding and digestion Gustatory nucleus cells project to Medulla : swallowing, salivation, gagging, vomitting Hypothalamus and Basal telencephalon : palatability, motivate to eat Lesions in the hypothalamus/amygdala, basal telencephalon : overeat or ignore food, alter preference for food types The Neural Coding of Taste Labeled line hypothesis Individual taste receptor cells for each stimuli In reality, most neurons are broadly tuned (they are less specific) Gustatory nucleus receive synapses from many axons of different taste axons Population coding Roughly labeled lines Large numbers of broadly tuned neurons Contribution of temperature and textural features of food Warns of harmful substances, combines with taste for identifying foods Pheromones a mode of communication Reproductive behavior Territorial boundaries Identification of individuals Signal aggression or submission Role of human pheromones unclear
  Question: What condition results from lesions in the VPM nucleus or primary gustatory cortex?
  Answer: Ageusia

Context: {0}
Now create a single short-answer question.

<|eot_id|>

<|start_header_id|>assistant<|end_header_id|>
"""
```
