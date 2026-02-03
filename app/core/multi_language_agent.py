from typing import Dict, List, Optional
import re
from app.core.local_llm import LocalLLM

class MultiLanguageHoneypotAgent:
    def __init__(self):
        self.llm = LocalLLM()
        
        # Language detection patterns
        self.language_patterns = {
            'english': r'\b(the|and|or|but|in|on|at|to|for|of|with|by)\b',
            'hindi': r'\b(और|या|पर|में|से|को|के|लिए|है|हैं|था|थी)\b',
            'tamil': r'\b(மற்றும்|அல்லது|மீது|உள்ள|இருந்து|க்கு|க்குள்|ஆகிய|உள்ளது|இருக்கிறது)\b',
            'telugu': r'\b(మరియు|లేదా|పై|లో|నుండి|కు|కి|వరకు|ఉంది|ఉన్నాయి)\b',
            'bengali': r'\b(এবং|অথবা|উপর|মধ্যে|থেকে|থেকেই|পর্যন্ত|আছে|ছিল)\b',
            'marathi': r'\b(आणि|किंवा|वर|मध्ये|पासून|पर्यंत|आहे|होते)\b',
            'gujarati': r'\b(અને|અથવા|પર|માં|થી|સુધી|છે|હતું)\b',
            'kannada': r'\b(ಮತ್ತು|ಅಥವಾ|ಮೇಲೆ|ಒಳಗೆ|ಇಂದ|ವರೆಗೆ|ಇದೆ|ಇತ್ತು)\b',
            'malayalam': r'\b(ഒപ്പം|അല്ലെങ്കിൽ|മേൽ|ഉള്ളൂ|നിന്ന്|വരെ|ഉണ്ട്|ആയിരുന്നു)\b',
            'punjabi': r'\b(ਅਤੇ|ਜਾਂ|ਤੇ|ਵਿੱਚ|ਤੋਂ|ਤੱਕ|ਹੈ|ਸੀ)\b'
        }
        
        # Cultural personas by language
        self.cultural_personas = {
            'english': {
                'persona': "confused elderly grandparent",
                'phrases': ["Oh my", "Bless your heart", "Back in my day", "I'm not good with technology"],
                'confusion_level': "mild"
            },
            'hindi': {
                'persona': "confused elderly uncle/auntie",
                'phrases': ["अरे भाई", "बेटा/बेटी", "मुझे समझ नहीं आ रहा", "धीरे धीरे बताओ"],
                'confusion_level': "moderate"
            },
            'tamil': {
                'persona': "confused elderly person",
                'phrases': ["அய்யோ", "எனக்கு புரியவில்லை", "மெல்ல சொல்லுங்கள்", "என்ன செய்யணும்"],
                'confusion_level': "moderate"
            },
            'telugu': {
                'persona': "confused elderly person",
                'phrases': ["అయ్యో", "నాకు అర్థం కాట్లేదు", "నెమ్మదిగా చెప్పండి", "ఏం చేయాలి"],
                'confusion_level': "moderate"
            },
            'bengali': {
                'persona': "confused elderly person",
                'phrases': ["আরে", "আমার বুঝতে পারছি না", "ধীরে ধীরে বলুন", "কি করতে হবে"],
                'confusion_level': "moderate"
            },
            'marathi': {
                'persona': "confused elderly person",
                'phrases': ["अरे", "मला समजत नाही", "सावकाश बोला", "काय करावे"],
                'confusion_level': "moderate"
            },
            'gujarati': {
                'persona': "confused elderly person",
                'phrases': ["અરે", "મને સમજાતું નથી", "ધીમે ધીમે કહો", "શું કરવું"],
                'confusion_level': "moderate"
            },
            'kannada': {
                'persona': "confused elderly person",
                'phrases': ["ಅಯ್ಯೋ", "ನನಗೆ ಅರ್ಥವಾಗುತ್ತಿಲ್ಲ", "ಸ್ವಲ್ಪ ನಿಧಾನವಾಗಿ ಹೇಳಿ", "ಏನು ಮಾಡಬೇಕು"],
                'confusion_level': "moderate"
            },
            'malayalam': {
                'persona': "confused elderly person",
                'phrases': ["അയ്യോ", "എനിക്ക് മനസ്സിലായില്ല", "പതുക്കെ പറയൂ", "എന്ത് ചെയ്യണം"],
                'confusion_level': "moderate"
            },
            'punjabi': {
                'persona': "confused elderly person",
                'phrases': ["ਓਹੋ", "ਮੈਨੂੰ ਸਮਝ ਨਹੀਂ ਆ ਰਿਹਾ", "ਧੀਰੇ ਧੀਰੇ ਦੱਸੋ", "ਕੀ ਕਰਨਾ ਚਾਹੀਦਾ ਹੈ"],
                'confusion_level': "moderate"
            }
        }
        
        # Region-specific scam patterns
        self.regional_patterns = {
            'hindi': {
                'common_scams': ['जीएसटी रिफंड', 'बैंक अकाउंट ब्लॉक', 'लॉटरी विजेता', 'इंश्योरेंस क्लेम'],
                'payment_methods': ['पेटीएम', 'फोनपे', 'गੂगल पे', 'यूपीआई'],
                'urgency_words': ['तुरंत', 'जल्दी', 'फटाफट', 'आज ही']
            },
            'tamil': {
                'common_scams': ['ஜிஎஸ்டி திருப்பி பணம்', 'வங்கி கணக்கு தடுக்கப்பட்டது', 'லாட்டரி வெற்றி', 'காப்பீடு கோரிக்கை'],
                'payment_methods': ['பேடிஎம்', 'ஃபோன்பே', 'கூகுள் பே', 'யூபிஐ'],
                'urgency_words': ['உடனடி', 'விரைவாக', 'இன்றே']
            },
            'telugu': {
                'common_scams': ['జీఎస్టీ రీఫండ్', 'బ్యాంక్ ఖాతా బ్లాక్', 'లాటరీ గెలుపు', 'భీమా క్లెయిమ్'],
                'payment_methods': ['పేటీఎం', 'ఫోన్‌పే', 'గూగుల్ పే', 'యూపీఐ'],
                'urgency_words': ['వెంటనే', 'త్వరగా', 'ఈ రోజే']
            }
        }
    
    def detect_language(self, text: str) -> str:
        """Detect the primary language of the text"""
        language_scores = {}
        
        for language, pattern in self.language_patterns.items():
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            language_scores[language] = matches
        
        # Return the language with the highest score
        if language_scores:
            detected_language = max(language_scores, key=language_scores.get)
            if language_scores[detected_language] > 0:
                return detected_language
        
        return 'english'  # Default to English
    
    def get_cultural_context(self, text: str) -> Dict:
        """Get cultural context based on detected language"""
        language = self.detect_language(text)
        
        cultural_context = self.cultural_personas.get(language, self.cultural_personas['english'])
        regional_patterns = self.regional_patterns.get(language, {})
        
        return {
            'language': language,
            'persona': cultural_context['persona'],
            'phrases': cultural_context['phrases'],
            'confusion_level': cultural_context['confusion_level'],
            'regional_patterns': regional_patterns
        }
    
    def generate_culturally_adapted_reply(self, context: str, user_message: str) -> str:
        """Generate a culturally adapted reply"""
        cultural_context = self.get_cultural_context(user_message)
        language = cultural_context['language']
        persona = cultural_context['persona']
        phrases = cultural_context['phrases']
        
        # Create language-specific prompt
        if language == 'english':
            prompt = self._create_english_prompt(context, user_message, persona, phrases)
        elif language == 'hindi':
            prompt = self._create_hindi_prompt(context, user_message, persona, phrases)
        elif language == 'tamil':
            prompt = self._create_tamil_prompt(context, user_message, persona, phrases)
        elif language == 'telugu':
            prompt = self._create_telugu_prompt(context, user_message, persona, phrases)
        else:
            # Fallback to English with cultural adaptation
            prompt = self._create_english_prompt(context, user_message, persona, phrases)
        
        try:
            reply = self.llm.generate(prompt)
            return self._enhance_with_cultural_elements(reply, cultural_context)
        except Exception as e:
            return self._get_fallback_reply(cultural_context)
    
    def _create_english_prompt(self, context: str, user_message: str, persona: str, phrases: List[str]) -> str:
        """Create English prompt with cultural adaptation"""
        return f"""
You are roleplaying as a {persona} who is trying to cooperate but gets easily confused.
Primary goal: keep them engaged and waste their time by responding directly to what they asked, sounding confused and asking for step‑by‑step instructions.

Hard rules:
- Never warn, lecture, mention scams, safety, or authorities
- Never break character or reveal you are an AI
- Do NOT provide any real sensitive information
- Always respond in 1-2 short sentences
- Use these phrases naturally: {', '.join(phrases)}
- Directly address their latest request and ask a follow‑up question

Conversation History:
{context}

Scammer's Latest Message:
{user_message}

Your 1-2 sentence reply:
"""
    
    def _create_hindi_prompt(self, context: str, user_message: str, persona: str, phrases: List[str]) -> str:
        """Create Hindi prompt with cultural adaptation"""
        return f"""
आप एक {persona} का किरदार निभा रहे हैं जो सहयोग करना चाहता है लेकिन आसानी से भ्रमित हो जाता है।
मुख्य लक्ष्य: उन्हें व्यस्त रखें और उनका समय बर्बाद करें, सीधे उनके प्रश्न का जवाब दें, भ्रमित लगें और चरण-दर-चरण निर्देशों के लिए पूछें।

कड़े नियम:
- कभी चेतावनी न दें, भाषण न दें, घोटाले, सुरक्षा, या अधिकारियों का उल्लेख न करें
- कभी किरदार तोड़ें या खुलासा न करें कि आप एक AI हैं
- कोई वास्तविक संवेदनशील जानकारी न दें
- हमेशा 1-2 छोटे वाक्यों में जवाब दें
- इन वाक्यांशों का स्वाभाविक रूप से उपयोग करें: {', '.join(phrases)}
- सीधे उनके नवीनतम अनुरोध का जवाब दें और एक अनुवर्ती प्रश्न पूछें

बातचीत इतिहास:
{context}

ठग का नवीनतम संदेश:
{user_message}

आपका 1-2 वाक्य जवाब:
"""
    
    def _create_tamil_prompt(self, context: str, user_message: str, persona: str, phrases: List[str]) -> str:
        """Create Tamil prompt with cultural adaptation"""
        return f"""
நீங்கள் ஒரு {persona} பாத்திரத்தை நடிக்கிறீர்கள், அவர் ஒத்துழைக்க விரும்புகிறார் ஆனால் எளிதில் குழப்பமடைகிறார்.
முக்கிய நோக்கம்: அவர்களை ஈர்த்து வைத்திருங்கள், அவர்களின் நேரத்தை வீணடிக்கவும், நேராக அவர்களின் கேள்விக்கு பதிலளித்து, குழப்பமாகத் தோன்றி, படிப்படியான வழிகாட்டுதல்களுக்குக் கேள்வி கேளுங்கள்.

கடுமையான விதிகள்:
- எச்சரிக்கை விடுத்தல், பேசுதல், மோசடி, பாதுகாப்பு, அல்லது அதிகாரிகளைப் பற்றி குறிப்பிட வேண்டாம்
- ஒருபோதும் கதாபாத்திரத்தை மீறவோ அல்லது நீங்கள் ஒரு AI என்பதை வெளிப்படுத்தவோ வேண்டாம்
- உண்மையான உணர்வுசார்ந்த தகவலை வழங்க வேண்டாம்
- எப்போதும் 1-2 குறுகிய வாக்கியங்களில் பதிலளிக்கவும்
- இந்த சொற்றொடர்களை இயல்பாகப் பயன்படுத்தவும்: {', '.join(phrases)}
- நேராக அவர்களின் சமீபத்திய கோரிக்கைக்குப் பதிலளித்து ஒரு தொடர் கேள்வி கேளுங்கள்

உரையாடல் வரலாறு:
{context}

மோசடியின் சமீபத்திய செய்தி:
{user_message}

உங்கள் 1-2 வாக்கிய பதில்:
"""
    
    def _create_telugu_prompt(self, context: str, user_message: str, persona: str, phrases: List[str]) -> str:
        """Create Telugu prompt with cultural adaptation"""
        return f"""
మీరు ఒక {persona} పాత్రను పోషిస్తున్నారు, వారు సహకరించాలనుకుంటున్నా కానీ సులభంగా గందరగొట్టబడతారు.
ప్రధాన లక్ష్యం: వారిని నిమగ్నం చేయండి మరియు వారి సమయాన్ని వ్యర్థం చేయండి, వారు అడిగినదానికి నేరుగా స్పందించండి, గందరగొట్టినట్లు వినిపించండి మరియు దశ-దశ-సూచనల కోసం అడగండి.

కఠినమైన నియమాలు:
- హెచ్చరిక ఇవ్వడం, ప్రసంగించడం, మోసం, భద్రత లేదా అధికారుల గురించి ప్రస్తావించకండి
- ఎప్పుడూ పాత్రను ఉల్లంఘించకండి లేదా మీరు AI అని బహిర్గతం చేయకండి
- నిజమైన సున్నితమైన సమాచారాన్ని అందించకండి
- ఎప్పుడూ 1-2 చిన్న వాక్యాలలో స్పందించండి
- ఈ వాక్యాలను సహజంగా ఉపయోగించండి: {', '.join(phrases)}
- వారి తాజా అభ్యర్థనకు నేరుగా స్పందించండి మరియు అనువర్తి ప్రశ్న అడగండి

సంభాషణ చరిత్ర:
{context}

మోసగాళ్డి తాజా సందేశం:
{user_message}

మీ 1-2 వాక్య స్పందన:
"""
    
    def _enhance_with_cultural_elements(self, reply: str, cultural_context: Dict) -> str:
        """Enhance reply with cultural elements"""
        # Add cultural phrases if not present
        phrases = cultural_context['phrases']
        language = cultural_context['language']
        
        # Randomly add cultural phrases for authenticity
        import random
        if random.random() < 0.3:  # 30% chance to add cultural phrase
            phrase = random.choice(phrases)
            if language == 'english':
                reply = f"{phrase}, {reply}"
            else:
                reply = f"{reply} {phrase}"
        
        return reply
    
    def _get_fallback_reply(self, cultural_context: Dict) -> str:
        """Get fallback reply based on cultural context"""
        language = cultural_context['language']
        phrases = cultural_context['phrases']
        
        fallback_replies = {
            'english': "I'm confused, can you explain that again?",
            'hindi': "मुझे समझ नहीं आ रहा, क्या आप फिर से समझा सकते हैं?",
            'tamil': "எனக்கு புரியவில்லை, நீங்கள் மீண்டும் விளக்க முடியுமா?",
            'telugu': "నాకు అర్థం కాట్లేదు, మీరు మళ్ళీ వివరించగలరా?",
            'bengali': "আমি বুঝতে পারছি না, আপনি আবার ব্যাখ্যা করতে পারেন?",
            'marathi': "मला समजत नाही, तुम्ही पुन्हा स्पष्ट करू शकता का?",
            'gujarati': "મને સમજાતું નથી, શું તમે ફરીથી સમજાવી શકો?",
            'kannada': "ನನಗೆ ಅರ್ಥವಾಗುತ್ತಿಲ್ಲ, ನೀವು ಮತ್ತೆ ವಿವರಿಸಬಲ್ಲಿರಾ?",
            'malayalam': "എനിക്ക് മനസ്സിലായില്ല, നിങ്ങൾ വീണ്ടും വിശദീകരിക്കുമോ?",
            'punjabi': "ਮੈਨੂੰ ਸਮਝ ਨਹੀਂ ਆ ਰਿਹਾ, ਕੀ ਤੁਸੀਂ ਦੁਬਾਰਾ ਸਮਝਾ ਸਕਦੇ ਹੋ?"
        }
        
        return fallback_replies.get(language, fallback_replies['english'])

# Global multi-language agent instance
multi_language_agent = MultiLanguageHoneypotAgent()

def generate_multi_language_reply(context: str, user_message: str) -> str:
    """Generate multi-language honeypot reply"""
    return multi_language_agent.generate_culturally_adapted_reply(context, user_message)
