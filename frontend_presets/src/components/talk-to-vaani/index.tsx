// import { Card } from "primereact/card"
// import "./index.css"
// import { IconField } from "primereact/iconfield";
// import { InputIcon } from "primereact/inputicon";
// import { InputText } from "primereact/inputtext";
// import { Button } from "primereact/button";
// import { Dropdown } from "primereact/dropdown";
// import { useEffect, useRef, useState } from "react";
// import { getAllModels, triggerCall, voiceOptions, maleVoices, femaleVoices } from "../../common/api";
// import { TriggerCallRequest } from "../../common/types";
// import { Toast } from "primereact/toast";
// import { useNavigate } from "react-router-dom";
// import { pagePaths } from "../../common/constants";
// import selectedMale from "../../assets/logos/selected_male.png";
// import notSelectedMale from "../../assets/logos/not_selected_male.png";
// import selectedFemale from "../../assets/logos/selected_female.png";
// import notSelectedFemale from "../../assets/logos/not_selected_female.png";

// type model = {
//     model_id: string,
//     model_name: string,
// }

// type CountryCode = {
//     code: string,
//     label: string,
// }

// const TalkToVaani = () => {
//     const navigate = useNavigate();
//     const toast = useRef<Toast>(null);

//     const show = (summary: string) => {
//         toast.current?.show({ severity: 'info', summary, life: 3000 });
//     };

//     const [loading, setLoading] = useState<boolean>(false);
//     const [formData, setFormData] = useState<any>({});
//     const [plans, setPlans] = useState<model[]>([]);
//     const [selectedPlan, setSelectedPlan] = useState<model | null>(null);
//     const [selectedCountryCode, setSelectedCountryCode] = useState<CountryCode>({ code: "+91", label: "+91" });
//     const [selectedVoice, setSelectedVoice] = useState<{label: string, value: string, gender: string} | null>(null);
//     const [selectedGender, setSelectedGender] = useState<string>('M'); // Default to Male

//     // List of common country codes (simplified)
//     const countryCodes: CountryCode[] = [
//         { code: "+1", label: "+1" },
//         { code: "+44", label: "+44" },
//         { code: "+91", label: "+91" },
//         { code: "+61", label: "+61" },
//         { code: "+86", label: "+86" },
//         { code: "+33", label: "+33" },
//         { code: "+49", label: "+49" },
//         { code: "+81", label: "+81" },
//         { code: "+7", label: "+7" },
//         { code: "+27", label: "+27" },
//         { code: "+971", label: "+971" },
//         { code: "+65", label: "+65" },
//         { code: "+60", label: "+60" },
//         { code: "+34", label: "+34" },
//         { code: "+39", label: "+39" },
//         { code: "+55", label: "+55" },
//         { code: "+82", label: "+82" },
//         { code: "+66", label: "+66" },
//         { code: "+63", label: "+63" },
//         { code: "+64", label: "+64" },
//         { code: "+351", label: "+351" },
//         { code: "+48", label: "+48" },
//         { code: "+420", label: "+420" },
//         { code: "+30", label: "+30" },
//         { code: "+351", label: "+351" }
//     ];

//     useEffect(() => {
//         getAllModels()
//             .then((data: any) => {
//                 setPlans(data.data);
//             })
//             .catch((error) => {
//                 console.error("Error fetching models:", error);
//             });
//     }, [])

//     const getFilteredVoices = () => {
//         const defaultOption = { label: 'Default', value: '', gender: 'N/A' };
        
//         if (selectedGender === 'M') {
//             return [defaultOption, ...maleVoices];
//         } else if (selectedGender === 'F') {
//             return [defaultOption, ...femaleVoices];
//         }
//         return voiceOptions;
//     };
//     console.log("Filtered Voices:", getFilteredVoices());

//     const handleGenderChange = (gender: string) => {
//     setSelectedGender(gender);
//     setSelectedVoice(null); // Reset selected voice when gender changes
//     };

//     const talkToVaani = async () => {
//         console.log("Selected Voice Full Object:", JSON.stringify(selectedVoice, null, 2));
//         console.log("Selected Voice:", selectedVoice);
//         console.log("Voice Value:", selectedVoice?.value);
//         setLoading(true);
//         if (selectedPlan && selectedPlan.model_id && formData && formData.contact_number && formData.name) {
//             const user = localStorage.getItem('fullName')
//             if (user) {
//                 const req: TriggerCallRequest = {
//                     agent_id: selectedPlan.model_id,
//                     contact_number: selectedCountryCode.code + formData.contact_number,
//                     name: formData.name,
//                     user_id: user,
//                     voice: selectedVoice?.value || ""
//                 }

//                 try {
//                     const res = await triggerCall(req);
//                     if (res.status <= 299) {
//                         // Clear form data and reset selected plan
//                         setFormData({});
//                         setSelectedPlan(null);
//                         setSelectedVoice(null);
//                         setSelectedGender('M');
//                         show("You will be called by our agent shortly.")
//                     } else {
//                         show("Something went wrong");
//                     }
//                 } catch (error) {
//                     console.error("Error triggering call:", error);
//                     show("Error triggering call. Please try again.");
//                 }
//             } else {
//                 show("Please login first");
//                 navigate(pagePaths.signin);
//             }
//         } else {
//             show("Please fill all required fields");
//         }
//         setLoading(false);
//     }

//     return (
//         <Card className="talk-to-vaani">
//             <Toast ref={toast} position="bottom-right" />
//             <h1>Talk to Vaani 1.0</h1>
//             <div>
//                 <IconField iconPosition="right">
//                     <InputIcon className="pi pi-user"> </InputIcon>
//                     <InputText 
//                         placeholder="your good name?" 
//                         value={formData.name || ""} 
//                         onChange={(e) => (setFormData({ ...formData, name: e.target.value }))}
//                         disabled={loading}
//                     />
//                 </IconField>
//                 <hr />
//             </div>

//             <div>
//                 <div className="phone-input-container">
//                     <div className="country-code-dropdown">
//                         <Dropdown
//                             value={selectedCountryCode}
//                             options={countryCodes}
//                             onChange={(e) => setSelectedCountryCode(e.value)}
//                             optionLabel="label"
//                             placeholder="+91"
//                             disabled={loading}
//                         />
//                     </div>
//                     <div className="phone-number-input">
//                         <IconField iconPosition="right">
//                             <InputIcon className="pi pi-phone"> </InputIcon>
//                             <InputText 
//                                 placeholder="Enter phone number" 
//                                 value={formData.contact_number || ""} 
//                                 onChange={(e) => (setFormData({ ...formData, contact_number: e.target.value }))} 
//                                 keyfilter="int"
//                                 disabled={loading}
//                             />
//                         </IconField>
//                     </div>
//                 </div>
//                 <hr />
//             </div>


//             <div>
//                 {/* <h3 style={{marginBottom: '0.5rem'}}>SPEAKER PREFERENCE:</h3> */}
//                 <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '0.5rem' }}>
//                     <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
//                         <div 
//                             onClick={() => !loading && handleGenderChange('M')}
//                             style={{
//                                 width: '50px',
//                                 height: '50px',
//                                 borderRadius: '50%',
//                                 display: 'flex',
//                                 alignItems: 'center',
//                                 justifyContent: 'center',
//                                 cursor: loading ? 'not-allowed' : 'pointer',
//                                 overflow: 'hidden',
//                                 transition: 'all 0.2s ease'
//                             }}
//                         >
//                             <img 
//                                 src={selectedGender === 'M' ? selectedMale : notSelectedMale}
//                                 alt="Male" 
//                                 style={{ width: '100%', height: '100%', objectFit: 'cover' }}
//                             />
//                         </div>
//                         <div 
//                             onClick={() => !loading && handleGenderChange('F')}
//                             style={{
//                                 width: '50px',
//                                 height: '50px',
//                                 borderRadius: '50%',
//                                 display: 'flex',
//                                 alignItems: 'center',
//                                 justifyContent: 'center',
//                                 cursor: loading ? 'not-allowed' : 'pointer',
//                                 overflow: 'hidden',
//                                 transition: 'all 0.2s ease'
//                             }}
//                         >
//                             <img 
//                                 src={selectedGender === 'F' ? selectedFemale : notSelectedFemale}
//                                 alt="Female" 
//                                 style={{ width: '100%', height: '100%', objectFit: 'cover' }}
//                             />
//                         </div>
//                     </div>
//                     <div style={{ flex: 1 }}>
//                         <Dropdown 
//                             value={selectedVoice?.label || null} // Show the label in UI
//                             onChange={(e) => {
//                                 const foundVoice = getFilteredVoices().find(voice => voice.label === e.value);
//                                 setSelectedVoice(foundVoice || null);
//                             }} 
//                             options={getFilteredVoices().map(voice => voice.label)} // Just use labels as options
//                             placeholder="Select a Voice" 
//                             className="w-full" 
//                             disabled={loading}
//                         />
//                     </div>
//                     {/* <div style={{ 
//                         width: '40px', 
//                         height: '40px', 
//                         display: 'flex', 
//                         alignItems: 'center', 
//                         justifyContent: 'center',
//                         cursor: 'pointer'
//                     }}>
//                         <i className="pi pi-search" style={{ fontSize: '18px', color: '#666' }}></i>
//                     </div> */}
//                 </div>
//                 <hr />
//             </div>

//             <h3>USE-CASE:</h3>
//             <div>
//                 <Dropdown 
//                     value={selectedPlan} 
//                     onChange={(e) => setSelectedPlan(e.value)} 
//                     options={plans} 
//                     optionLabel="model_name"
//                     placeholder="Select a Plan" 
//                     className="w-full md:w-14rem" 
//                     disabled={loading}
//                 />
//                 <hr />
//             </div>

//             <Button 
//                 label="TRIGGER TEST CALL" 
//                 icon="pi pi-phone" 
//                 severity="secondary" 
//                 onClick={talkToVaani} 
//                 disabled={(!selectedPlan || !formData.contact_number || !formData.name) || loading}
//                 loading={loading}
//             />
//         </Card>
//     );
// };

// export default TalkToVaani;




// frontend/src/components/talk-to-vaani/index.tsx
import { Card } from "primereact/card"
import "./index.css"
import { IconField } from "primereact/iconfield";
import { InputIcon } from "primereact/inputicon";
import { InputText } from "primereact/inputtext";
import { Button } from "primereact/button";
import { Dropdown } from "primereact/dropdown";
import { useEffect, useRef, useState } from "react";
import { getAllModels, triggerCall, voiceOptions, maleVoices, femaleVoices } from "../../common/api";
import { TriggerCallRequest } from "../../common/types";
import { Toast } from "primereact/toast";
import { useNavigate } from "react-router-dom";
import { ConditionalWrapper } from "../ConditionalWrapper"; // Fixed import
import { CONFIG } from "../../config/appConfig"; // Fixed import
import selectedMale from "../../assets/logos/selected_male.png";
import notSelectedMale from "../../assets/logos/not_selected_male.png";
import selectedFemale from "../../assets/logos/selected_female.png";
import notSelectedFemale from "../../assets/logos/not_selected_female.png";

type model = {
    model_id: string,
    model_name: string,
}

type CountryCode = {
    code: string,
    label: string,
}

const TalkToVaani = () => {
    const navigate = useNavigate();
    const toast = useRef<Toast>(null);

    const show = (summary: string) => {
        toast.current?.show({ severity: 'info', summary, life: 3000 });
    };

    const [loading, setLoading] = useState<boolean>(false);
    const [formData, setFormData] = useState<any>({});
    const [plans, setPlans] = useState<model[]>([]);
    const [selectedPlan, setSelectedPlan] = useState<model | null>(null);
    const [selectedCountryCode, setSelectedCountryCode] = useState<CountryCode>({ code: "+91", label: "+91" });
    const [selectedVoice, setSelectedVoice] = useState<{label: string, value: string, gender: string} | null>(null);
    const [selectedGender, setSelectedGender] = useState<string>('M'); // Default to Male

    // Country codes - only load if country code selector is enabled
    const countryCodes: CountryCode[] = [
        { code: "+1", label: "+1" },
        { code: "+44", label: "+44" },
        { code: "+91", label: "+91" },
        { code: "+61", label: "+61" },
        { code: "+86", label: "+86" },
        { code: "+33", label: "+33" },
        { code: "+49", label: "+49" },
        { code: "+81", label: "+81" },
        { code: "+7", label: "+7" },
        { code: "+27", label: "+27" },
        { code: "+971", label: "+971" },
        { code: "+65", label: "+65" },
        { code: "+60", label: "+60" },
        { code: "+34", label: "+34" },
        { code: "+39", label: "+39" },
        { code: "+55", label: "+55" },
        { code: "+82", label: "+82" },
        { code: "+66", label: "+66" },
        { code: "+63", label: "+63" },
        { code: "+64", label: "+64" },
        { code: "+351", label: "+351" },
        { code: "+48", label: "+48" },
        { code: "+420", label: "+420" },
        { code: "+30", label: "+30" }
    ];

    useEffect(() => {
        if (CONFIG.components.call_test.talk_to_vaani.use_case_dropdown) {
            getAllModels()
                .then((data: any) => {
                    setPlans(data.data);
                })
                .catch((error) => {
                    console.error("Error fetching models:", error);
                });
        }
    }, [])

    const getFilteredVoices = () => {
        if (!CONFIG.components.call_test.talk_to_vaani.voice_options_dropdown) {
            return [];
        }
        
        const defaultOption = { label: 'Default', value: '', gender: 'N/A' };
        
        if (selectedGender === 'M') {
            return [defaultOption, ...maleVoices];
        } else if (selectedGender === 'F') {
            return [defaultOption, ...femaleVoices];
        }
        return voiceOptions;
    };

    const handleGenderChange = (gender: string) => {
        if (!CONFIG.components.call_test.talk_to_vaani.voice_selection) return;
        
        setSelectedGender(gender);
        setSelectedVoice(null); // Reset selected voice when gender changes
    };

    const talkToVaani = async () => {
        if (!CONFIG.components.call_test.talk_to_vaani.trigger_call_button) return;
        
        setLoading(true);
        
        // Validate required fields based on config
        const requiredFieldsValid = (
            (!CONFIG.components.call_test.talk_to_vaani.name_field || formData.name) &&
            (!CONFIG.components.call_test.talk_to_vaani.phone_number_field || formData.contact_number) &&
            (!CONFIG.components.call_test.talk_to_vaani.use_case_dropdown || selectedPlan?.model_id)
        );

        if (!requiredFieldsValid) {
            show("Please fill all required fields");
            setLoading(false);
            return;
        }

        const user = localStorage.getItem('fullName')
        if (user && selectedPlan?.model_id) {
            const contactNumber = CONFIG.components.call_test.talk_to_vaani.country_code_selector 
                ? selectedCountryCode.code + formData.contact_number
                : formData.contact_number;

            const req: TriggerCallRequest = {
                agent_id: selectedPlan.model_id,
                contact_number: contactNumber,
                name: formData.name || "User",
                user_id: user,
                voice: (CONFIG.components.call_test.talk_to_vaani.voice_options_dropdown && selectedVoice?.value) || ""
            }

            try {
                const res = await triggerCall(req);
                if (res.status <= 299) {
                    // Clear form data and reset selected plan
                    setFormData({});
                    setSelectedPlan(null);
                    setSelectedVoice(null);
                    setSelectedGender('M');
                    show("You will be called by our agent shortly.")
                } else {
                    show("Something went wrong");
                }
            } catch (error) {
                console.error("Error triggering call:", error);
                show("Error triggering call. Please try again.");
            }
        } else {
            show("Please login first");
            navigate("/sign-in"); // Fixed: Direct string instead of pagePaths
        }
        setLoading(false);
    }

    return (
        <Card className="talk-to-vaani">
            <Toast ref={toast} position="bottom-right" />
            <h1>Talk to Vaani 1.0</h1>
            
            {/* Name Field */}
            <ConditionalWrapper condition="call_test.talk_to_vaani.name_field">
                <div>
                    <IconField iconPosition="right">
                        <InputIcon className="pi pi-user"> </InputIcon>
                        <InputText 
                            placeholder="your good name?" 
                            value={formData.name || ""} 
                            onChange={(e) => (setFormData({ ...formData, name: e.target.value }))}
                            disabled={loading}
                        />
                    </IconField>
                    <hr />
                </div>
            </ConditionalWrapper>

            {/* Phone Number Field */}
            <ConditionalWrapper condition="call_test.talk_to_vaani.phone_number_field">
                <div>
                    <div className="phone-input-container">
                        <ConditionalWrapper condition="call_test.talk_to_vaani.country_code_selector">
                            <div className="country-code-dropdown">
                                <Dropdown
                                    value={selectedCountryCode}
                                    options={countryCodes}
                                    onChange={(e) => setSelectedCountryCode(e.value)}
                                    optionLabel="label"
                                    placeholder="+91"
                                    disabled={loading}
                                />
                            </div>
                        </ConditionalWrapper>
                        
                        <div className="phone-number-input">
                            <IconField iconPosition="right">
                                <InputIcon className="pi pi-phone"> </InputIcon>
                                <InputText 
                                    placeholder="Enter phone number" 
                                    value={formData.contact_number || ""} 
                                    onChange={(e) => (setFormData({ ...formData, contact_number: e.target.value }))} 
                                    keyfilter="int"
                                    disabled={loading}
                                />
                            </IconField>
                        </div>
                    </div>
                    <hr />
                </div>
            </ConditionalWrapper>

            {/* Voice Selection */}
            <ConditionalWrapper condition="call_test.talk_to_vaani.voice_selection">
                <div>
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                            <div 
                                onClick={() => !loading && handleGenderChange('M')}
                                style={{
                                    width: '50px',
                                    height: '50px',
                                    borderRadius: '50%',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    cursor: loading ? 'not-allowed' : 'pointer',
                                    overflow: 'hidden',
                                    transition: 'all 0.2s ease'
                                }}
                            >
                                <img 
                                    src={selectedGender === 'M' ? selectedMale : notSelectedMale}
                                    alt="Male" 
                                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                />
                            </div>
                            <div 
                                onClick={() => !loading && handleGenderChange('F')}
                                style={{
                                    width: '50px',
                                    height: '50px',
                                    borderRadius: '50%',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    cursor: loading ? 'not-allowed' : 'pointer',
                                    overflow: 'hidden',
                                    transition: 'all 0.2s ease'
                                }}
                            >
                                <img 
                                    src={selectedGender === 'F' ? selectedFemale : notSelectedFemale}
                                    alt="Female" 
                                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                />
                            </div>
                        </div>
                        
                        <ConditionalWrapper condition="call_test.talk_to_vaani.voice_options_dropdown">
                            <div style={{ flex: 1 }}>
                                <Dropdown 
                                    value={selectedVoice?.label || null}
                                    onChange={(e) => {
                                        const foundVoice = getFilteredVoices().find(voice => voice.label === e.value);
                                        setSelectedVoice(foundVoice || null);
                                    }} 
                                    options={getFilteredVoices().map(voice => voice.label)}
                                    placeholder="Select a Voice" 
                                    className="w-full" 
                                    disabled={loading}
                                />
                            </div>
                        </ConditionalWrapper>
                    </div>
                    <hr />
                </div>
            </ConditionalWrapper>

            {/* Use Case Dropdown */}
            <ConditionalWrapper condition="call_test.talk_to_vaani.use_case_dropdown">
                <div>
                    <h3>USE-CASE:</h3>
                    <Dropdown 
                        value={selectedPlan} 
                        onChange={(e) => setSelectedPlan(e.value)} 
                        options={plans} 
                        optionLabel="model_name"
                        placeholder="Select a Plan" 
                        className="w-full md:w-14rem" 
                        disabled={loading}
                    />
                    <hr />
                </div>
            </ConditionalWrapper>

            {/* Trigger Call Button */}
            <ConditionalWrapper condition="call_test.talk_to_vaani.trigger_call_button">
                <Button 
                    label="TRIGGER TEST CALL" 
                    icon="pi pi-phone" 
                    severity="secondary" 
                    onClick={talkToVaani} 
                    disabled={loading}
                    loading={loading}
                />
            </ConditionalWrapper>
        </Card>
    );
};

export default TalkToVaani;