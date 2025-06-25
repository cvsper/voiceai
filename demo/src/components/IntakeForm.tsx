import React, { useState, Children, Fragment } from 'react';
import { ProgressChecklist } from './ProgressChecklist';
import { FileUpload } from './FileUpload';
import { PaymentInstructions } from './PaymentInstructions';
import { ReminderNotice } from './ReminderNotice';
import { CheckIcon, ArrowLeftIcon, ArrowRightIcon, SaveIcon } from 'lucide-react';
interface IntakeFormProps {
  language: string;
}
export const IntakeForm: React.FC<IntakeFormProps> = ({
  language
}) => {
  const [formData, setFormData] = useState({
    fullName: '',
    ssn: '',
    hasUploadedId: false,
    routingNumber: '',
    accountNumber: '',
    filingWithChildren: false,
    children: [{
      name: '',
      dob: '',
      ssn: ''
    }]
  });
  const [currentStep, setCurrentStep] = useState(1);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const translations = {
    steps: {
      en: ['Personal Information', 'Bank Details', 'Children Information', 'Documents Upload', 'Review & Submit'],
      es: ['Información Personal', 'Detalles Bancarios', 'Información de Niños', 'Carga de Documentos', 'Revisar y Enviar']
    },
    personalInfo: {
      en: {
        title: 'Personal Information',
        fullName: 'Full Name',
        ssn: 'Social Security Number or ITIN',
        idUpload: 'Upload Government-issued ID',
        uploadButton: 'Upload ID'
      },
      es: {
        title: 'Información Personal',
        fullName: 'Nombre Completo',
        ssn: 'Número de Seguro Social o ITIN',
        idUpload: 'Subir Identificación Oficial',
        uploadButton: 'Subir ID'
      }
    },
    bankInfo: {
      en: {
        title: 'Bank Information for Direct Deposit',
        routing: 'Routing Number',
        account: 'Account Number'
      },
      es: {
        title: 'Información Bancaria para Depósito Directo',
        routing: 'Número de Ruta',
        account: 'Número de Cuenta'
      }
    },
    childrenInfo: {
      en: {
        title: 'Children Information',
        question: 'Are you filing with children?',
        yes: 'Yes',
        no: 'No',
        childName: "Child's Full Name",
        childDob: 'Date of Birth',
        childSsn: "Child's Social Security Number",
        addChild: 'Add Another Child'
      },
      es: {
        title: 'Información de Niños',
        question: '¿Está declarando con niños?',
        yes: 'Sí',
        no: 'No',
        childName: 'Nombre Completo del Niño',
        childDob: 'Fecha de Nacimiento',
        childSsn: 'Número de Seguro Social del Niño',
        addChild: 'Añadir Otro Niño'
      }
    },
    documents: {
      en: {
        title: 'Upload Tax Documents',
        subtitle: 'Please upload your W-2s, 1099s, and any other relevant tax documents'
      },
      es: {
        title: 'Subir Documentos Fiscales',
        subtitle: 'Por favor suba sus W-2, 1099 y cualquier otro documento fiscal relevante'
      }
    },
    review: {
      en: {
        title: 'Review & Submit',
        subtitle: 'Please review your information before submitting',
        personalSection: 'Personal Information',
        bankSection: 'Bank Information',
        childrenSection: 'Children Information',
        documentsSection: 'Uploaded Documents',
        submitButton: 'Submit Tax Information'
      },
      es: {
        title: 'Revisar y Enviar',
        subtitle: 'Por favor revise su información antes de enviar',
        personalSection: 'Información Personal',
        bankSection: 'Información Bancaria',
        childrenSection: 'Información de Niños',
        documentsSection: 'Documentos Subidos',
        submitButton: 'Enviar Información Fiscal'
      }
    },
    navigation: {
      en: {
        back: 'Back',
        next: 'Next',
        save: 'Save Progress'
      },
      es: {
        back: 'Atrás',
        next: 'Siguiente',
        save: 'Guardar Progreso'
      }
    }
  };
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const {
      name,
      value,
      type,
      checked
    } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  const handleChildInputChange = (index: number, field: string, value: string) => {
    const updatedChildren = [...formData.children];
    updatedChildren[index] = {
      ...updatedChildren[index],
      [field]: value
    };
    setFormData(prev => ({
      ...prev,
      children: updatedChildren
    }));
  };
  const addChild = () => {
    setFormData(prev => ({
      ...prev,
      children: [...prev.children, {
        name: '',
        dob: '',
        ssn: ''
      }]
    }));
  };
  const handleFileUpload = (files: File[]) => {
    setUploadedFiles(prev => [...prev, ...files]);
    // If ID was uploaded in step 1
    if (currentStep === 1) {
      setFormData(prev => ({
        ...prev,
        hasUploadedId: true
      }));
    }
  };
  const progressItems = [{
    id: 'personal',
    label: {
      en: 'Personal Information',
      es: 'Información Personal'
    },
    completed: !!formData.fullName && !!formData.ssn,
    required: true
  }, {
    id: 'id',
    label: {
      en: 'Government ID',
      es: 'Identificación Oficial'
    },
    completed: formData.hasUploadedId,
    required: true
  }, {
    id: 'bank',
    label: {
      en: 'Bank Information',
      es: 'Información Bancaria'
    },
    completed: !!formData.routingNumber && !!formData.accountNumber,
    required: true
  }, {
    id: 'children',
    label: {
      en: 'Children Information',
      es: 'Información de Niños'
    },
    completed: !formData.filingWithChildren || formData.filingWithChildren && formData.children.length > 0 && formData.children.every(child => !!child.name && !!child.dob && !!child.ssn),
    required: formData.filingWithChildren
  }, {
    id: 'documents',
    label: {
      en: 'Tax Documents',
      es: 'Documentos Fiscales'
    },
    completed: uploadedFiles.length > 0,
    required: true
  }];
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return renderPersonalInfo();
      case 2:
        return renderBankInfo();
      case 3:
        return renderChildrenInfo();
      case 4:
        return renderDocumentsUpload();
      case 5:
        return renderReview();
      default:
        return null;
    }
  };
  const renderPersonalInfo = () => {
    const t = translations.personalInfo[language as keyof typeof translations.personalInfo];
    return <div>
        <h2 className="text-2xl font-semibold mb-6">{t.title}</h2>
        <div className="space-y-6">
          <div>
            <label className="block text-gray-700 mb-2">{t.fullName}</label>
            <input type="text" name="fullName" value={formData.fullName} onChange={handleInputChange} className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
          </div>
          <div>
            <label className="block text-gray-700 mb-2">{t.ssn}</label>
            <input type="text" name="ssn" value={formData.ssn} onChange={handleInputChange} className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="XXX-XX-XXXX" />
          </div>
          <div>
            <label className="block text-gray-700 mb-2">{t.idUpload}</label>
            <FileUpload language={language} onFileUpload={handleFileUpload} />
          </div>
        </div>
      </div>;
  };
  const renderBankInfo = () => {
    const t = translations.bankInfo[language as keyof typeof translations.bankInfo];
    return <div>
        <h2 className="text-2xl font-semibold mb-6">{t.title}</h2>
        <div className="space-y-6">
          <div>
            <label className="block text-gray-700 mb-2">{t.routing}</label>
            <input type="text" name="routingNumber" value={formData.routingNumber} onChange={handleInputChange} className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
          </div>
          <div>
            <label className="block text-gray-700 mb-2">{t.account}</label>
            <input type="text" name="accountNumber" value={formData.accountNumber} onChange={handleInputChange} className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
          </div>
        </div>
      </div>;
  };
  const renderChildrenInfo = () => {
    const t = translations.childrenInfo[language as keyof typeof translations.childrenInfo];
    return <div>
        <h2 className="text-2xl font-semibold mb-6">{t.title}</h2>
        <div className="space-y-6">
          <div>
            <label className="block text-gray-700 mb-2">{t.question}</label>
            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input type="checkbox" name="filingWithChildren" checked={formData.filingWithChildren} onChange={handleInputChange} className="w-5 h-5 text-blue-600" />
                <span className="ml-2">{t.yes}</span>
              </label>
            </div>
          </div>
          {formData.filingWithChildren && <div className="space-y-6">
              {formData.children.map((child, index) => <div key={index} className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                  <h3 className="font-medium mb-4">Child {index + 1}</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-gray-700 mb-2">
                        {t.childName}
                      </label>
                      <input type="text" value={child.name} onChange={e => handleChildInputChange(index, 'name', e.target.value)} className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                    </div>
                    <div>
                      <label className="block text-gray-700 mb-2">
                        {t.childDob}
                      </label>
                      <input type="date" value={child.dob} onChange={e => handleChildInputChange(index, 'dob', e.target.value)} className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                    </div>
                    <div>
                      <label className="block text-gray-700 mb-2">
                        {t.childSsn}
                      </label>
                      <input type="text" value={child.ssn} onChange={e => handleChildInputChange(index, 'ssn', e.target.value)} className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="XXX-XX-XXXX" />
                    </div>
                  </div>
                </div>)}
              <button type="button" onClick={addChild} className="text-blue-600 hover:text-blue-800 font-medium flex items-center">
                <span className="mr-2">+</span>
                {t.addChild}
              </button>
            </div>}
        </div>
      </div>;
  };
  const renderDocumentsUpload = () => {
    const t = translations.documents[language as keyof typeof translations.documents];
    return <div>
        <h2 className="text-2xl font-semibold mb-2">{t.title}</h2>
        <p className="text-gray-600 mb-6">{t.subtitle}</p>
        <FileUpload language={language} onFileUpload={handleFileUpload} />
        <PaymentInstructions language={language} />
      </div>;
  };
  const renderReview = () => {
    const t = translations.review[language as keyof typeof translations.review];
    return <div>
        <h2 className="text-2xl font-semibold mb-2">{t.title}</h2>
        <p className="text-gray-600 mb-6">{t.subtitle}</p>
        <div className="space-y-8">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-medium text-gray-800 mb-3">
              {t.personalSection}
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">
                  {translations.personalInfo[language as keyof typeof translations.personalInfo].fullName}
                </p>
                <p className="font-medium">{formData.fullName || '—'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">
                  {translations.personalInfo[language as keyof typeof translations.personalInfo].ssn}
                </p>
                <p className="font-medium">{formData.ssn || '—'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">
                  {translations.personalInfo[language as keyof typeof translations.personalInfo].idUpload}
                </p>
                <p className="font-medium">
                  {formData.hasUploadedId ? <span className="flex items-center text-green-600">
                      <CheckIcon className="w-4 h-4 mr-1" />
                      Uploaded
                    </span> : '—'}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-medium text-gray-800 mb-3">{t.bankSection}</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">
                  {translations.bankInfo[language as keyof typeof translations.bankInfo].routing}
                </p>
                <p className="font-medium">{formData.routingNumber || '—'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">
                  {translations.bankInfo[language as keyof typeof translations.bankInfo].account}
                </p>
                <p className="font-medium">{formData.accountNumber || '—'}</p>
              </div>
            </div>
          </div>
          {formData.filingWithChildren && <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-medium text-gray-800 mb-3">
                {t.childrenSection}
              </h3>
              {formData.children.map((child, index) => <div key={index} className="border-t border-gray-200 pt-3 mt-3 first:border-0 first:pt-0 first:mt-0">
                  <h4 className="text-sm font-medium">Child {index + 1}</h4>
                  <div className="grid md:grid-cols-3 gap-4 mt-2">
                    <div>
                      <p className="text-xs text-gray-500">
                        {translations.childrenInfo[language as keyof typeof translations.childrenInfo].childName}
                      </p>
                      <p className="font-medium">{child.name || '—'}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">
                        {translations.childrenInfo[language as keyof typeof translations.childrenInfo].childDob}
                      </p>
                      <p className="font-medium">{child.dob || '—'}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">
                        {translations.childrenInfo[language as keyof typeof translations.childrenInfo].childSsn}
                      </p>
                      <p className="font-medium">{child.ssn || '—'}</p>
                    </div>
                  </div>
                </div>)}
            </div>}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-medium text-gray-800 mb-3">
              {t.documentsSection}
            </h3>
            {uploadedFiles.length > 0 ? <ul className="space-y-1">
                {uploadedFiles.map((file, index) => <li key={index} className="flex items-center">
                    <FileIcon className="w-4 h-4 text-blue-500 mr-2" />
                    <span className="text-sm">{file.name}</span>
                  </li>)}
              </ul> : <p className="text-gray-500 text-sm">No documents uploaded</p>}
          </div>
          <ReminderNotice language={language} />
          <div className="flex justify-center">
            <button type="button" className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg flex items-center transition-colors">
              {t.submitButton}
              <CheckIcon className="ml-2 w-5 h-5" />
            </button>
          </div>
        </div>
      </div>;
  };
  return <div className="max-w-4xl mx-auto">
      {/* Steps indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {translations.steps[language as keyof typeof translations.steps].map((step, index) => <Fragment key={index}>
                {index > 0 && <div className="hidden sm:block w-full h-1 bg-gray-200">
                    <div className="h-1 bg-blue-600" style={{
              width: currentStep > index ? '100%' : '0%'
            }}></div>
                  </div>}
                <div className="relative flex flex-col items-center">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center
                    ${currentStep > index ? 'bg-blue-600 text-white' : currentStep === index + 1 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'}`}>
                    {currentStep > index ? <CheckIcon className="w-5 h-5" /> : index + 1}
                  </div>
                  <span className="mt-2 text-xs text-center hidden sm:block">
                    {step}
                  </span>
                </div>
              </Fragment>)}
        </div>
      </div>
      <div className="bg-white rounded-lg shadow-lg p-6 md:p-8 mb-8">
        {renderStepContent()}
      </div>
      <div className="flex justify-between items-center">
        <button type="button" onClick={() => setCurrentStep(prev => Math.max(1, prev - 1))} disabled={currentStep === 1} className={`flex items-center ${currentStep === 1 ? 'text-gray-400 cursor-not-allowed' : 'text-blue-600 hover:text-blue-800'}`}>
          <ArrowLeftIcon className="w-5 h-5 mr-1" />
          {translations.navigation[language as keyof typeof translations.navigation].back}
        </button>
        <button type="button" className="flex items-center text-gray-600 hover:text-gray-800">
          <SaveIcon className="w-5 h-5 mr-1" />
          {translations.navigation[language as keyof typeof translations.navigation].save}
        </button>
        <button type="button" onClick={() => setCurrentStep(prev => Math.min(5, prev + 1))} disabled={currentStep === 5} className={`flex items-center ${currentStep === 5 ? 'text-gray-400 cursor-not-allowed' : 'text-blue-600 hover:text-blue-800'}`}>
          {translations.navigation[language as keyof typeof translations.navigation].next}
          <ArrowRightIcon className="w-5 h-5 ml-1" />
        </button>
      </div>
      <div className="mt-8">
        <ProgressChecklist items={progressItems} language={language} />
      </div>
    </div>;
};