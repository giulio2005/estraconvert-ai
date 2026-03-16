'use client';

import Link from 'next/link';
import { FileSpreadsheet, Upload, File, Euro, Table, Clock, Bug, Zap, Shield, Puzzle, ArrowRight, Check, Eye, Bell, Settings, Star, Bot, AlertTriangle } from 'lucide-react';
import Header from '@/components/layout/Header';
import Footer from '@/components/layout/Footer';

export default function HomePage() {
  return (
    <div className="bg-gray-50 font-inter">
      <Header />

      <main>
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-[600px] py-20 overflow-hidden">
          <div className="max-w-7xl mx-auto px-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              <div className="space-y-8">
                <h2 className="text-4xl lg:text-5xl font-bold text-gray-900 leading-tight">
                  Converti i tuoi <span className="text-blue-600">estratti conto</span> in CSV
                </h2>
                <p className="text-lg lg:text-xl text-gray-600 leading-relaxed">
                  Trasforma facilmente i tuoi estratti conto bancari in formato CSV pronto per essere importato nei tuoi gestionali aziendali.
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                  <Link
                    href="/convert"
                    className="bg-blue-600 text-white px-8 py-4 rounded-xl font-semibold text-lg hover:bg-blue-700 transition-all transform hover:scale-105 shadow-lg flex items-center justify-center space-x-3"
                  >
                    <Upload size={20} />
                    <span>Carica il tuo file</span>
                  </Link>
                  <button className="border-2 border-gray-300 text-gray-700 px-8 py-4 rounded-xl font-semibold text-lg hover:border-gray-400 transition-colors">
                    Prova demo
                  </button>
                </div>
              </div>
              <div className="hidden lg:flex justify-center lg:justify-end">
                <div className="relative w-full max-w-[500px]">
                  <div className="w-64 xl:w-80 h-80 xl:h-96 bg-white rounded-2xl shadow-2xl p-6 xl:p-8 transform rotate-3">
                    <div className="space-y-4">
                      <div className="flex items-center space-x-3">
                        <File className="text-red-500" size={24} />
                        <span className="text-gray-700 font-medium text-sm xl:text-base">Estratto_conto.pdf</span>
                      </div>
                      <div className="h-px bg-gray-200"></div>
                      <div className="space-y-3">
                        <div className="h-4 bg-gray-200 rounded"></div>
                        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                      </div>
                    </div>
                  </div>
                  <div className="absolute -right-4 xl:-right-8 top-12 w-12 h-12 xl:w-16 xl:h-16 bg-blue-600 rounded-full flex items-center justify-center">
                    <ArrowRight className="text-white" size={20} />
                  </div>
                  <div className="absolute -right-16 xl:-right-24 -bottom-8 w-64 xl:w-80 h-56 xl:h-64 bg-green-50 rounded-2xl shadow-xl p-4 xl:p-6 transform -rotate-2">
                    <div className="flex items-center space-x-3 mb-4">
                      <FileSpreadsheet className="text-green-600" size={20} />
                      <span className="text-gray-700 font-medium text-sm xl:text-base">estratto_convertito.csv</span>
                    </div>
                    <div className="space-y-2">
                      <div className="grid grid-cols-3 gap-2 text-xs text-gray-600">
                        <span>Data</span>
                        <span>Descrizione</span>
                        <span>Importo</span>
                      </div>
                      <div className="space-y-1">
                        <div className="grid grid-cols-3 gap-2 text-xs bg-white p-2 rounded">
                          <span>01/10/23</span>
                          <span>Bonifico</span>
                          <span>+1,250.00</span>
                        </div>
                        <div className="grid grid-cols-3 gap-2 text-xs bg-white p-2 rounded">
                          <span>02/10/23</span>
                          <span>Pagamento</span>
                          <span>-85.50</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Problem Section */}
        <section className="py-20 bg-white">
          <div className="max-w-6xl mx-auto px-6">
            <div className="text-center mb-16">
              <h3 className="text-4xl font-bold text-gray-900 mb-6">Ancora copia e incolla?</h3>
              <p className="text-2xl text-gray-600 mb-4">Scambia il lavoro inutile con lavoro produttivo.</p>
              <p className="text-lg text-gray-500 max-w-3xl mx-auto">I dati negli estratti conto sono non strutturati e difficili da riutilizzare. L&apos;estrazione manuale è lenta, soggetta a errori e costosa.</p>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
              <div className="space-y-8">
                <div className="bg-red-50 border border-red-200 rounded-xl p-6">
                  <div className="flex items-center space-x-3 mb-4">
                    <AlertTriangle className="text-red-500" size={20} />
                    <h4 className="text-lg font-semibold text-red-800">Problemi del processo manuale</h4>
                  </div>
                  <ul className="space-y-3 text-red-700">
                    <li className="flex items-center space-x-3">
                      <Clock className="text-red-500" size={16} />
                      <span>Ore di lavoro sprecate in copia-incolla</span>
                    </li>
                    <li className="flex items-center space-x-3">
                      <Bug className="text-red-500" size={16} />
                      <span>Errori umani e dati inconsistenti</span>
                    </li>
                    <li className="flex items-center space-x-3">
                      <Euro className="text-red-500" size={16} />
                      <span>Costi elevati per il data entry</span>
                    </li>
                  </ul>
                </div>
              </div>
              <div className="relative group">
                <div className="overflow-hidden rounded-2xl shadow-2xl border-4 border-red-100 transition-all group-hover:border-red-300 group-hover:shadow-red-200">
                  <video
                    className="w-full h-96 object-cover transition-transform group-hover:scale-105"
                    autoPlay
                    loop
                    muted
                    playsInline
                  >
                    <source src="/traditional.mp4" type="video/mp4" />
                  </video>
                </div>
                <div className="absolute -top-6 -right-6 w-20 h-20 bg-gradient-to-br from-red-500 to-red-600 rounded-full flex items-center justify-center shadow-xl animate-pulse">
                  <span className="text-white text-3xl font-bold">×</span>
                </div>
                <div className="absolute -bottom-4 -left-4 bg-white px-6 py-3 rounded-xl shadow-lg border-2 border-red-200">
                  <p className="text-sm font-semibold text-red-600">Metodo tradizionale</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Solution Section */}
        <section className="py-20 bg-gradient-to-br from-blue-50 to-indigo-100">
          <div className="max-w-6xl mx-auto px-6">
            <div className="text-center mb-16">
              <h3 className="text-4xl font-bold text-gray-900 mb-6">Sfrutta i dati presenti nei tuoi estratti conto</h3>
              <p className="text-xl text-gray-600 max-w-4xl mx-auto">Converti automaticamente PDF bancari, estratti conto e altri documenti finanziari non strutturati in dati CSV strutturati che puoi scaricare o inviare direttamente ai tuoi gestionali e flussi di lavoro.</p>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-16">
              <div className="bg-white p-8 rounded-2xl shadow-sm text-center">
                <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <File className="text-blue-600" size={32} />
                </div>
                <h4 className="text-xl font-semibold text-gray-900 mb-4">Documenti non strutturati</h4>
                <p className="text-gray-600">PDF, immagini, estratti conto di qualsiasi banca</p>
              </div>
              <div className="bg-white p-8 rounded-2xl shadow-sm text-center relative">
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <ArrowRight className="text-white" size={16} />
                </div>
                <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6 mt-8">
                  <Bot className="text-green-600" size={32} />
                </div>
                <h4 className="text-xl font-semibold text-gray-900 mb-4">IA di conversione</h4>
                <p className="text-gray-600">Algoritmi avanzati di riconoscimento ed estrazione</p>
              </div>
              <div className="bg-white p-8 rounded-2xl shadow-sm text-center">
                <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Table className="text-purple-600" size={32} />
                </div>
                <h4 className="text-xl font-semibold text-gray-900 mb-4">Dati strutturati</h4>
                <p className="text-gray-600">CSV puliti pronti per i tuoi sistemi</p>
              </div>
            </div>
            <div className="bg-white rounded-2xl p-8 shadow-lg">
              <div className="text-center mb-8">
                <h4 className="text-2xl font-bold text-gray-900 mb-4">EstraConvert trasforma i tuoi estratti in dati puliti e strutturati</h4>
                <p className="text-lg text-gray-600">Pronti per i tuoi gestionali aziendali</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                <div className="relative group">
                  <div className="overflow-hidden rounded-xl shadow-lg border-2 border-blue-100 transition-all group-hover:border-blue-300">
                    <video
                      className="w-full h-64 object-cover transition-transform group-hover:scale-105"
                      autoPlay
                      loop
                      muted
                      playsInline
                    >
                      <source src="/Area.mp4" type="video/mp4" />
                    </video>
                  </div>
                  <div className="absolute -top-3 -right-3 w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-full flex items-center justify-center shadow-lg">
                    <Check className="text-white" size={20} />
                  </div>
                </div>
                <div className="space-y-6">
                  <div className="flex items-start space-x-4">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                      <Check className="text-blue-600" size={16} />
                    </div>
                    <div>
                      <h5 className="font-semibold text-gray-900 mb-2">Formattazione automatica</h5>
                      <p className="text-gray-600">Date, importi e descrizioni perfettamente strutturati</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-4">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                      <Check className="text-blue-600" size={16} />
                    </div>
                    <div>
                      <h5 className="font-semibold text-gray-900 mb-2">Compatibilità universale</h5>
                      <p className="text-gray-600">Funziona con Excel, SAP, QuickBooks e altri</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-4">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                      <Check className="text-blue-600" size={16} />
                    </div>
                    <div>
                      <h5 className="font-semibold text-gray-900 mb-2">Zero errori di trascrizione</h5>
                      <p className="text-gray-600">Precisione del 99.9% nell&apos;estrazione dei dati</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Savings Section */}
        <section className="py-20 bg-white">
          <div className="max-w-6xl mx-auto px-6">
            <div className="text-center mb-16">
              <h3 className="text-4xl font-bold text-gray-900 mb-6">Risparmia fino al 98% sul data entry con l&apos;IA</h3>
              <p className="text-xl text-gray-600 max-w-4xl mx-auto">Lascia che sia l&apos;IA a fare il lavoro noioso ed estragga i dati dai tuoi estratti conto in modo automatico e affidabile. È più veloce e più preciso del lavoro manuale e ti permette di risparmiare significativamente sui costi.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
              <div className="text-center">
                <div className="text-4xl font-bold text-blue-600 mb-2">98%</div>
                <div className="text-gray-600">Riduzione tempo di elaborazione</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-green-600 mb-2">99.9%</div>
                <div className="text-gray-600">Precisione nell&apos;estrazione</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-purple-600 mb-2">24/7</div>
                <div className="text-gray-600">Disponibilità del servizio</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-orange-600 mb-2">5sec</div>
                <div className="text-gray-600">Tempo medio di conversione</div>
              </div>
            </div>
          </div>
        </section>

        {/* Testimonial Section */}
        <section className="py-20 bg-gray-50 overflow-hidden">
          <div className="max-w-6xl mx-auto px-6">
            <div className="text-center mb-16">
              <h3 className="text-3xl font-bold text-gray-900 mb-4">Cosa dicono i nostri clienti</h3>
              <p className="text-lg text-gray-600">Migliaia di aziende si fidano di EstraConvert</p>
            </div>
            <div className="space-y-8">
              {/* First Row - Scroll Left */}
              <div className="flex space-x-6 animate-scroll-left">
                {[
                  { name: 'Maria Rossi', role: 'CFO, TechCorp Italia', text: 'Abbiamo automatizzato l\'elaborazione di migliaia di estratti conto ogni mese. Risparmio incredibile di tempo e zero errori.', avatar: '1' },
                  { name: 'Giuseppe Bianchi', role: 'Responsabile Amministrativo, LogiFlow', text: 'La precisione è impressionante. Non torniamo più al processo manuale, questo tool ha rivoluzionato il nostro workflow.', avatar: '2' },
                  { name: 'Andrea Verdi', role: 'Founder, StartupFinance', text: 'Semplicità d\'uso incredibile. In 5 minuti ho convertito mesi di estratti conto. Servizio fantastico!', avatar: '3' },
                  { name: 'Francesca Neri', role: 'Controller, MegaCorp', text: 'Il ROI è stato immediato. Abbiamo ridotto i costi del data entry del 90% e migliorato l\'accuratezza dei dati.', avatar: '5' },
                ].map((testimonial, i) => (
                  <div key={i} className="bg-white p-6 rounded-xl shadow-sm min-w-[400px] flex-shrink-0">
                    <div className="flex items-center mb-4">
                      <img src={`https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-${testimonial.avatar}.jpg`} alt={testimonial.name} className="w-12 h-12 rounded-full mr-4" />
                      <div>
                        <h5 className="font-semibold text-gray-900">{testimonial.name}</h5>
                        <p className="text-gray-600 text-sm">{testimonial.role}</p>
                      </div>
                    </div>
                    <p className="text-gray-700">&quot;{testimonial.text}&quot;</p>
                    <div className="flex text-yellow-400 mt-3">
                      {[...Array(5)].map((_, i) => <Star key={i} size={16} fill="currentColor" />)}
                    </div>
                  </div>
                ))}
              </div>

              {/* Second Row - Scroll Right */}
              <div className="flex space-x-6 animate-scroll-right">
                {[
                  { name: 'Marco Russo', role: 'Direttore Finanziario, InnovaTech', text: 'Integrazione perfetta con i nostri sistemi ERP. La qualità dei dati estratti è superiore al lavoro manuale.', avatar: '4' },
                  { name: 'Elena Conti', role: 'Head of Operations, DataFlow', text: 'Supporto clienti eccezionale e risultati sempre affidabili. È diventato uno strumento essenziale per noi.', avatar: '6' },
                  { name: 'Roberto Ferrari', role: 'CEO, SmartFinance', text: 'Game changer per il nostro business. Abbiamo scalato le operazioni senza aumentare il team amministrativo.', avatar: '8' },
                  { name: 'Silvia Moretti', role: 'Finance Manager, CloudSystems', text: 'Velocità e precisione incredibili. Quello che prima richiedeva giorni ora si fa in minuti.', avatar: '7' },
                ].map((testimonial, i) => (
                  <div key={i} className="bg-white p-6 rounded-xl shadow-sm min-w-[400px] flex-shrink-0">
                    <div className="flex items-center mb-4">
                      <img src={`https://storage.googleapis.com/uxpilot-auth.appspot.com/avatars/avatar-${testimonial.avatar}.jpg`} alt={testimonial.name} className="w-12 h-12 rounded-full mr-4" />
                      <div>
                        <h5 className="font-semibold text-gray-900">{testimonial.name}</h5>
                        <p className="text-gray-600 text-sm">{testimonial.role}</p>
                      </div>
                    </div>
                    <p className="text-gray-700">&quot;{testimonial.text}&quot;</p>
                    <div className="flex text-yellow-400 mt-3">
                      {[...Array(5)].map((_, i) => <Star key={i} size={16} fill="currentColor" />)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 bg-gray-50">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-16">
              <h3 className="text-3xl font-bold text-gray-900 mb-4">Perché scegliere EstraConvert</h3>
              <p className="text-lg text-gray-600">Semplice, veloce e sicuro</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="bg-white p-8 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                <div className="w-16 h-16 bg-blue-100 rounded-xl flex items-center justify-center mb-6">
                  <Zap className="text-blue-600" size={28} />
                </div>
                <h4 className="text-xl font-semibold text-gray-900 mb-4">Conversione istantanea</h4>
                <p className="text-gray-600">Ottieni il tuo file CSV in pochi secondi, pronto per l&apos;importazione.</p>
              </div>
              <div className="bg-white p-8 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                <div className="w-16 h-16 bg-green-100 rounded-xl flex items-center justify-center mb-6">
                  <Shield className="text-green-600" size={28} />
                </div>
                <h4 className="text-xl font-semibold text-gray-900 mb-4">Sicurezza garantita</h4>
                <p className="text-gray-600">I tuoi dati sono protetti e non vengono mai salvati sui nostri server.</p>
              </div>
              <div className="bg-white p-8 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                <div className="w-16 h-16 bg-purple-100 rounded-xl flex items-center justify-center mb-6">
                  <Puzzle className="text-purple-600" size={28} />
                </div>
                <h4 className="text-xl font-semibold text-gray-900 mb-4">Compatibilità totale</h4>
                <p className="text-gray-600">Funziona con tutti i principali gestionali e software contabili.</p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 bg-blue-600">
          <div className="max-w-4xl mx-auto px-6 text-center">
            <h3 className="text-3xl font-bold text-white mb-4">Pronto per iniziare?</h3>
            <p className="text-xl text-blue-100 mb-8">Converti il tuo primo estratto conto gratuitamente</p>
            <Link
              href="/convert"
              className="inline-block bg-white text-blue-600 px-8 py-4 rounded-xl font-semibold text-lg hover:bg-gray-50 transition-colors transform hover:scale-105"
            >
              Inizia ora
            </Link>
          </div>
        </section>
      </main>

      <Footer />

      <style jsx>{`
        @keyframes scroll-left {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        @keyframes scroll-right {
          0% { transform: translateX(-50%); }
          100% { transform: translateX(0); }
        }
        .animate-scroll-left {
          animation: scroll-left 30s linear infinite;
        }
        .animate-scroll-right {
          animation: scroll-right 30s linear infinite;
        }
        .animate-scroll-left:hover,
        .animate-scroll-right:hover {
          animation-play-state: paused;
        }
      `}</style>
    </div>
  );
}
