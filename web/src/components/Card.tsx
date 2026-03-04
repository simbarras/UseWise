interface CardProps { title: string; description: string; }

export default function Card({ title, description }: CardProps) {
  return (
    <div className="group bg-white p-6 rounded-2xl border border-slate-100 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
      <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-600 transition-colors">
        <span className="text-blue-600 group-hover:text-white">✨</span>
      </div>
      <h3 className="text-lg font-bold text-slate-800">{title}</h3>
      <p className="text-slate-500 text-sm mt-2 leading-relaxed">{description}</p>
    </div>
  );
}